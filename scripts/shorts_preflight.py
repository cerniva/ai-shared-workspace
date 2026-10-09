#!/usr/bin/env python3
"""Fail-closed MP4 gate. Requires ffmpeg/ffprobe; never uploads or spends credits.

Usage: python3 shorts_preflight.py VIDEO [--review REVIEW.json]
Review is independent evidence tied to sha256, with reviewer and checks:
speech_intelligible, audio_visual_sync, text_readable, facts_verified,
rights_checked, correct_channel, duplicate_checked (all boolean true).
With --manifest render.json, production_gates add required review checks:
hook_storyboard_checked (hook_storyboard gate) and moving_footage_checked
(moving_footage gate); both must be boolean true, set by an independent
reviewer after inspecting the real final MP4 (intake/chatgpt/2026-10-10-
shorts-review-schema.md). Missing/false/non-bool => ready=false.
Technical success alone is NOT approval. Exit 0=ready, 2=blocked.
Keep output/review private; do not commit private media or account data.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess


def run(args):
    return subprocess.run(args, capture_output=True, text=True, check=True, timeout=180)


# Render-manifest production_gates (set by shorts_learnings) -> review checks that
# must be independently true. A flag alone is never evidence (HO-20261010-11).
MANIFEST_GATE_REVIEW_CHECKS = {
    'hook_storyboard_qc_required': ('hook_storyboard_checked',),
    'rights_qc_required': ('rights_checked',),
    'full_mp4_qc_required': ('speech_intelligible', 'audio_visual_sync', 'text_readable'),
    'moving_footage_only': ('moving_footage_checked',),
}


# Independent review fields required by the hook_storyboard / moving_footage gates
# (ChatGPT spec da6bdc4). Only an independent reviewer who inspected the final MP4
# may set them true; the render pipeline must never self-approve.
REVIEW_GATE_FIELDS = {
    'hook_storyboard_checked': 'hook_storyboard_qc_required',
    'moving_footage_checked': 'moving_footage_only',
}


def review_check_status(review, key):
    """Classify one review check: 'true', 'missing', 'false' or 'not_boolean'."""
    checks = review.get('checks') if isinstance(review, dict) else None
    if not isinstance(checks, dict) or checks.get(key) is None:
        return 'missing'
    value = checks[key]
    if value is True:
        return 'true'
    if value is False:
        return 'false'
    return 'not_boolean'


def review_gate_evidence(manifest, review):
    """Status of REVIEW_GATE_FIELDS whose manifest gate is on; {} if none required."""
    gates = manifest.get('production_gates') if isinstance(manifest, dict) else None
    if not isinstance(gates, dict):
        return {}
    return {key: review_check_status(review, key)
            for key, gate in REVIEW_GATE_FIELDS.items() if gates.get(gate) is True}


def manifest_gate_blockers(manifest, review):
    """Return blockers for manifest gates that lack independent review evidence."""
    if manifest is None:
        return []
    if not isinstance(manifest, dict) or not isinstance(manifest.get('production_gates'), dict):
        return ['manifest_gates_invalid']
    checks = (review or {}).get('checks', {}) if isinstance(review, dict) else {}
    blockers = []
    for gate, value in manifest['production_gates'].items():
        if value is not True or gate not in MANIFEST_GATE_REVIEW_CHECKS:
            continue
        for key in MANIFEST_GATE_REVIEW_CHECKS[gate]:
            if checks.get(key) is not True:
                blockers.append('gate_' + gate + '_' + key)
    # Explicit, reason-bearing blockers for the two independent review fields.
    for key, status in review_gate_evidence(manifest, review).items():
        if status != 'true':
            blockers.append('review_' + key + '_' + status)
    return blockers


def inspect(path, review=None, manifest=None):
    report = {"schema": 1, "ready": False, "blockers": [], "checks": {}}
    try:
        digest = hashlib.sha256()
        with path.open('rb') as src:
            for chunk in iter(lambda: src.read(1024 * 1024), b''):
                digest.update(chunk)
        report['sha256'] = digest.hexdigest()
        data = json.loads(run(['ffprobe', '-v', 'error', '-show_streams',
                               '-show_format', '-of', 'json', str(path)]).stdout)
        video = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
        audio = next((s for s in data['streams'] if s['codec_type'] == 'audio'), None)
        duration = float(data['format'].get('duration', 0))
        report['duration_seconds'] = duration
        checks = report['checks']
        checks['duration'] = math.isfinite(duration) and 0 < duration <= 180
        checks['video_h264'] = bool(video and video.get('codec_name') == 'h264')
        checks['portrait_9_16'] = bool(video and video.get('width', 0) * 16 == video.get('height', 0) * 9)
        checks['audio_aac'] = bool(audio and audio.get('codec_name') == 'aac')
        # Decode the entire file, not just its header.
        run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(path),
             '-map', '0:v:0', '-map', '0:a:0?', '-f', 'null', '-'])
        checks['full_decode'] = True
        checks['audio_signal'] = False
        if audio:
            result = run(['ffmpeg', '-hide_banner', '-i', str(path), '-map', '0:a:0',
                          '-af', 'volumedetect', '-vn', '-f', 'null', '-'])
            match = re.search(r'mean_volume:\s*(-?inf|[-\d.]+) dB', result.stderr)
            if match:
                mean = float(match.group(1))
                report['mean_dbfs'] = mean if math.isfinite(mean) else None
                # Operational floor only; not a speech or mastering quality score.
                checks['audio_signal'] = math.isfinite(mean) and mean > -50
        report['blockers'].extend(k for k, ok in checks.items() if not ok)
        required = ['speech_intelligible', 'audio_visual_sync', 'text_readable',
                    'facts_verified', 'rights_checked', 'correct_channel', 'duplicate_checked']
        if not review:
            report['blockers'].append('independent_review_missing')
        elif review.get('sha256') != report['sha256'] or not review.get('reviewer'):
            report['blockers'].append('review_identity_mismatch')
        else:
            for key in required:
                if review.get('checks', {}).get(key) is not True:
                    report['blockers'].append('review_' + key)
        report['blockers'].extend(b for b in manifest_gate_blockers(manifest, review)
                                  if b not in report['blockers'])
        report['manifest_gates_checked'] = bool(
            isinstance(manifest, dict) and isinstance(manifest.get('production_gates'), dict))
        report['review_gate_evidence'] = review_gate_evidence(manifest, review)
        report['ready'] = not report['blockers']
    except (OSError, ValueError, KeyError, StopIteration, subprocess.SubprocessError) as exc:
        report['blockers'].append('inspection_failed_' + type(exc).__name__)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video', type=Path)
    parser.add_argument('--review', type=Path)
    parser.add_argument('--manifest', type=Path, help='render.json; its production_gates need review evidence')
    args = parser.parse_args()
    try:
        review = json.loads(args.review.read_text()) if args.review else None
        if review is not None and not isinstance(review, dict):
            raise ValueError('Review must be an object')
        manifest = json.loads(args.manifest.read_text()) if args.manifest else None
        result = inspect(args.video.resolve(), review, manifest)
    except (OSError, ValueError) as exc:
        result = {'ready': False, 'blockers': ['invalid_review_' + type(exc).__name__]}
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0 if result['ready'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
