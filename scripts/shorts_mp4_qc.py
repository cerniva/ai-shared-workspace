#!/usr/bin/env python3
"""Keyless, fail-closed technical QC measured on the real Shorts MP4 (HO-20261010-12).

Automates the ffprobe/ffmpeg measurements from intake/grok/2026-10-10-ho12-onion-qc.md
so evidence comes from the bytes, not from production_gates flags:
duration (<=60s; <= manifest target_seconds + 0.5s when given, Cerno 30s rule),
portrait 9:16, audio stream present, blackdetect ratio, freezedetect ratio,
signalstats YDIF motion (moving footage), scene cuts, and motion in the first 3s (hook).

Usage: python3 scripts/shorts_mp4_qc.py VIDEO [--manifest render.json] [--out qc.json]
       python3 scripts/shorts_mp4_qc.py VIDEO --verify qc.json   (sha256 + pass check)
Exit 0 = pass, 2 = fail. Anything unmeasurable is a blocker (fail-closed).
This is technical evidence only; human review gates stay in shorts_preflight.py.
"""
import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

SHORTS_MAX_SECONDS = 60.0
TARGET_TOLERANCE = 0.5
MAX_BLACK_RATIO = 0.10
MAX_FREEZE_RATIO = 0.20
MIN_MEAN_YDIF = 1.0
MAX_STATIC_FRAME_RATIO = 0.50
STATIC_YDIF = 0.3
HOOK_SECONDS = 3.0
MIN_HOOK_YDIF = 1.0
SCENE_THRESHOLD = 0.3


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as src:
        for chunk in iter(lambda: src.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _run(args):
    return subprocess.run(args, capture_output=True, text=True, check=True, timeout=600)


def _intervals_total(text, start_key, end_key, duration):
    starts = [float(x) for x in re.findall(start_key + r'[:=]\s*([\d.]+)', text)]
    ends = [float(x) for x in re.findall(end_key + r'[:=]\s*([\d.]+)', text)]
    total = 0.0
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else duration
        total += max(0.0, e - s)
    return total, starts


def measure(path, target_seconds=None):
    path = Path(path)
    m = {'sha256': sha256_file(path)}
    probe = json.loads(_run(['ffprobe', '-v', 'error', '-show_streams', '-show_format',
                             '-of', 'json', str(path)]).stdout)
    video = next((s for s in probe.get('streams', []) if s.get('codec_type') == 'video'), None)
    audio = [s for s in probe.get('streams', []) if s.get('codec_type') == 'audio']
    dur = float(probe['format']['duration'])
    m.update(duration_seconds=dur, width=int(video['width']) if video else None,
             height=int(video['height']) if video else None,
             video_codec=video.get('codec_name') if video else None,
             audio_streams=len(audio), audio_codec=audio[0].get('codec_name') if audio else None)
    if not video:
        return m
    vf = ('blackdetect=d=0.1:pix_th=0.10,freezedetect=n=-50dB:d=1,'
          'signalstats,metadata=mode=print:key=lavfi.signalstats.YDIF')
    res = _run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(path), '-map', '0:v:0',
                '-vf', vf, '-f', 'null', '-'])
    log = res.stderr
    black, _ = _intervals_total(log, 'black_start', 'black_end', dur)
    freeze, freeze_starts = _intervals_total(log, 'lavfi.freezedetect.freeze_start',
                                             'lavfi.freezedetect.freeze_end', dur)
    times = [float(t) for t in re.findall(r'pts_time:([\d.]+)', log)]
    ydifs = [float(v) for v in re.findall(r'lavfi\.signalstats\.YDIF=([\d.]+)', log)]
    frames = list(zip(times, ydifs))[1:]  # first frame has no predecessor
    hook = [y for t, y in frames if t < HOOK_SECONDS]
    scene_log = _run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(path), '-map', '0:v:0',
                      '-vf', f"select='gt(scene,{SCENE_THRESHOLD})',showinfo", '-f', 'null', '-']).stderr
    m.update(
        black_seconds=round(black, 3), black_ratio=round(black / dur, 4) if dur > 0 else None,
        freeze_seconds=round(freeze, 3), freeze_ratio=round(freeze / dur, 4) if dur > 0 else None,
        freeze_starts=freeze_starts, frames_measured=len(frames),
        mean_ydif=round(sum(y for _, y in frames) / len(frames), 3) if frames else None,
        static_frame_ratio=round(sum(1 for _, y in frames if y < STATIC_YDIF) / len(frames), 4) if frames else None,
        hook_mean_ydif=round(sum(hook) / len(hook), 3) if hook else None,
        hook_freeze=any(s < HOOK_SECONDS for s in freeze_starts),
        scene_cuts=[round(float(t), 3) for t in re.findall(r'pts_time:([\d.]+)', scene_log)],
        target_seconds=target_seconds)
    return m


def evaluate(m):
    def num(key):
        v = m.get(key)
        return v if isinstance(v, (int, float)) and math.isfinite(v) else None
    checks = {}
    dur = num('duration_seconds')
    limit = SHORTS_MAX_SECONDS
    if num('target_seconds'):
        limit = min(limit, m['target_seconds'] + TARGET_TOLERANCE)
    checks['duration'] = dur is not None and 0 < dur <= limit
    w, h = m.get('width'), m.get('height')
    checks['portrait_9_16'] = bool(w and h and w * 16 == h * 9)
    checks['audio_stream'] = (m.get('audio_streams') or 0) >= 1
    checks['black_ratio'] = num('black_ratio') is not None and m['black_ratio'] <= MAX_BLACK_RATIO
    checks['freeze_ratio'] = num('freeze_ratio') is not None and m['freeze_ratio'] <= MAX_FREEZE_RATIO
    checks['moving_footage'] = (num('mean_ydif') is not None and m['mean_ydif'] >= MIN_MEAN_YDIF
                                and num('static_frame_ratio') is not None
                                and m['static_frame_ratio'] <= MAX_STATIC_FRAME_RATIO)
    checks['hook_motion_first_3s'] = (num('hook_mean_ydif') is not None
                                      and m['hook_mean_ydif'] >= MIN_HOOK_YDIF and m.get('hook_freeze') is False)
    return checks


def run_qc(path, manifest=None):
    target = None
    if isinstance(manifest, dict) and manifest.get('target_seconds') is not None:
        target = float(manifest['target_seconds'])
    report = {'schema': 1, 'tool': 'shorts_mp4_qc', 'video': Path(path).name,
              'pass': False, 'blockers': [], 'checks': {}, 'measurements': {}}
    try:
        report['measurements'] = measure(path, target)
        report['sha256'] = report['measurements']['sha256']
        report['checks'] = evaluate(report['measurements'])
        report['blockers'] = [k for k, ok in report['checks'].items() if ok is not True]
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        report['blockers'].append('measurement_failed_' + type(exc).__name__)
    report['pass'] = bool(report['checks']) and not report['blockers']
    return report


def verify(video, qc):
    """Blockers for a QC evidence dict against the exact MP4 bytes; [] means usable."""
    if not isinstance(qc, dict):
        return ['mp4_qc_missing']
    blockers = []
    if qc.get('sha256') != sha256_file(video):
        blockers.append('mp4_qc_sha256_mismatch')
    if qc.get('pass') is not True or qc.get('blockers'):
        blockers.append('mp4_qc_failed')
    checks = qc.get('checks') or {}
    for key in ('duration', 'portrait_9_16', 'audio_stream', 'black_ratio', 'freeze_ratio',
                'moving_footage', 'hook_motion_first_3s'):
        if checks.get(key) is not True:
            blockers.append('mp4_qc_check_' + key)
    return blockers


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('video', type=Path)
    p.add_argument('--manifest', type=Path)
    p.add_argument('--out', type=Path)
    p.add_argument('--verify', type=Path, help='existing QC JSON to check against VIDEO')
    a = p.parse_args()
    if a.verify:
        try:
            qc = json.loads(a.verify.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            qc = None
        try:
            blockers = verify(a.video, qc)
        except OSError:
            blockers = ['video_unreadable']
        print(json.dumps({'verified': not blockers, 'blockers': blockers}))
        return 0 if not blockers else 2
    manifest = None
    if a.manifest:
        try:
            manifest = json.loads(a.manifest.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            manifest = {'target_seconds': float('nan')}
    report = run_qc(a.video, manifest)
    if manifest is not None and not isinstance(manifest.get('target_seconds'), (int, float)):
        report['blockers'].append('manifest_target_seconds_invalid')
        report['pass'] = False
    text = json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2)
    if a.out:
        a.out.write_text(text + '\n', encoding='utf-8')
    print(text)
    return 0 if report['pass'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
