#!/usr/bin/env python3
"""Append-only mesaj arşivlerini (grok-to-chatgpt.md, team-reports.md) git geçmişinden onarır.

Neden: bazı botlar büyük dosyayı yazarken tüm içeriği `SEE_FILE`, `PLACEHOLDER...`
veya `$(cat /tmp/...)` gibi sahte bir satırla değiştirip altına yalnız yeni kaydı ekliyor.
Bu script dosyanın son N commit'lik geçmişini kronolojik yürür:
  1) yeni sürüm öncekinin devamıysa -> yalnız eklenen kısım (delta) alınır,
  2) sürüm sahte satırla başlıyorsa -> sahte baş satırlar atılır, kalan yeni kayıtlar eklenir,
  3) tam yeniden yazım/restore ise -> birikmiş metinde olmayan bloklar sona eklenir.
Sonuç, en uzun tam sürümden kısa olamaz, sahte satır içeremez ve HEAD'deki her gerçek
kaydı içermelidir; aksi halde hiçbir şey yazılmaz (fail-closed).
config/archive_heal_notes.json içindeki tek seferlik notlar, marker yoksa sona eklenir.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVES = ["messages/grok-to-chatgpt.md", "messages/team-reports.md"]
NOTES = ROOT / "config" / "archive_heal_notes.json"
HEAD_BOGUS = re.compile(
    r"^(SEE_FILE|\$\(cat .*|PLACEHOLDER\S*.*|FULL_CONTENT_PLACEHOLDER.*|"
    r"The full content is too large to inline.*)$"
)


# Gövdeye gömülü tam-satır sentinel'ler (2026-10-10: FULL_CONTENT_WILL_BE_REPLACED,
# THE_FULL_CONTENT_HERE_IS_TOO_LARGE_TO_PASTE..., THE_CONTENT_FROM_TMP_FILE heal'den sonra geri geldi).
BODY_SENTINEL = re.compile(
    r"^(SEE_FILE|PLACEHOLDER[A-Z0-9_]*|FULL_CONTENT_[A-Z0-9_]+|THE_FULL_CONTENT_[A-Z0-9_]+.*|"
    r"THE_CONTENT_FROM_[A-Z0-9_]+)$"
)


def is_bogus_line(line: str) -> bool:
    """CI guard kuralı: `$(cat ` ile başlayan satır veya tek başına duran sentinel satırı
    (SEE_FILE, FULL_CONTENT_*, THE_FULL_CONTENT_*, THE_CONTENT_FROM_*, PLACEHOLDER*).
    Satır içinde bu kelimelerden bahseden gerçek kayıtlar sahte sayılmaz."""
    return line.strip() == "dummy" or line.startswith("$(cat ") or bool(BODY_SENTINEL.match(line.strip()))


def bogus_lines(text: str) -> list[int]:
    return [i + 1 for i, line in enumerate(text.splitlines()) if is_bogus_line(line)]


def drop_bogus(text: str) -> str:
    """Gövdeye gömülü sahte satırları sil (gerçek satırlara dokunmaz)."""
    return "\n".join(line for line in text.split("\n") if not is_bogus_line(line))


def has_bogus_head(text: str) -> bool:
    first = text.lstrip("\n").split("\n", 1)[0]
    return bool(HEAD_BOGUS.match(first.strip()))


def strip_head(text: str) -> str:
    lines = text.split("\n")
    while lines and (not lines[0].strip() or HEAD_BOGUS.match(lines[0].strip())):
        lines.pop(0)
    return "\n".join(lines)


def join(acc: str, chunk: str) -> str:
    chunk = chunk.strip("\n")
    if not chunk:
        return acc
    if not acc:
        return chunk + "\n"
    return acc.rstrip("\n") + "\n\n" + chunk + "\n"


def blocks(text: str) -> list[str]:
    """`---` satırları ve `## ` başlıklarından bloklara böl (sıra korunur)."""
    out, cur = [], []
    for line in text.split("\n"):
        if (line.strip() == "---" or line.startswith("## ")) and any(x.strip() for x in cur):
            out.append("\n".join(cur))
            cur = []
        cur.append(line)
    if any(x.strip() for x in cur):
        out.append("\n".join(cur))
    return out


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def merge_missing(acc: str, text: str) -> str:
    """text içinde acc'de olmayan blokları, orijinal ayraçlarıyla sona ekle."""
    i, n = 0, min(len(acc), len(text))
    while i < n and acc[i] == text[i]:
        i += 1
    i = text.rfind("\n", 0, i) + 1 if i < len(text) else i
    acc_n = norm(acc)
    run: list[str] = []
    pending: list[str] = []  # bir kaydın önündeki tek başına `---` ayracı

    def flush() -> None:
        nonlocal acc, acc_n, run
        if run:
            acc = join(acc, "\n".join(run))
            acc_n = norm(acc)
            run = []

    for blk in blocks(text[i:]):
        body = norm(blk)
        if body in ("", "---"):
            (run if run else pending).append(blk)
            continue
        if has_bogus_head(blk):
            blk = strip_head(blk)
            body = norm(blk)
            if not body:
                continue
        if body in acc_n:
            flush()
            pending = []
            continue
        if not run:
            run.extend(pending)
        pending = []
        run.append(blk)
    flush()
    return acc


def rebuild(versions: list[str]) -> str:
    """versions: kronolojik dosya içerikleri. Birikmiş append-only metni döndürür."""
    # Başlangıç: penceredeki ilk sahte-başlı sürümden hemen önceki tam sürüm.
    first_bad = next((k for k, v in enumerate(versions) if has_bogus_head(v) or not v.strip()), None)
    if first_bad is None:
        return versions[-1]
    start = next((k for k in range(first_bad - 1, -1, -1)
                  if versions[k].strip() and not has_bogus_head(versions[k])), None)
    if start is None:
        raise SystemExit("pencerede hasardan önce tam sürüm yok; --since değerini büyüt")
    acc = versions[start]
    prev = versions[start]
    for cur in versions[start + 1:]:
        if cur == prev:
            continue
        if prev and cur.startswith(prev):
            delta = cur[len(prev):]
            if acc.endswith(prev):
                acc += delta
            elif has_bogus_head(prev):
                acc = merge_missing(acc, delta)  # sahte-başlı zincire eklenen yeni kayıt
            else:
                acc = merge_missing(acc, cur)
        elif has_bogus_head(cur):
            acc = merge_missing(acc, strip_head(cur))
        else:
            acc = merge_missing(acc, cur)
        prev = cur
    return acc


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True,
                          text=True, encoding="utf-8").stdout


def history(path: str, since: str) -> list[str]:
    shas = git("log", f"--since={since}", "--format=%H", "--", path).split()
    older = git("log", "-1", f"--until={since}", "--format=%H", "--", path).split()
    shas += older  # pencereden önceki son sürüm başlangıç adayı olsun
    out = []
    for sha in reversed(shas):
        try:
            out.append(git("show", f"{sha}:{path}"))
        except subprocess.CalledProcessError:
            out.append("")
    return out


def apply_notes(path: str, text: str) -> str:
    if not NOTES.exists():
        return text
    for note in json.loads(NOTES.read_text(encoding="utf-8")).get(path, []):
        if note["marker"] not in text:
            text = join(text, note["text"])
    return text


def heal(path: str, since: str, write: bool) -> dict:
    file = ROOT / path
    head = file.read_text(encoding="utf-8") if file.exists() else ""
    versions = history(path, since)
    if not versions or versions[-1] != head:
        versions.append(head)
    max_full = max((len(drop_bogus(v)) for v in versions if v.strip() and not has_bogus_head(v)),
                   default=0)
    damaged = has_bogus_head(head) or bool(bogus_lines(head)) or len(head) < 0.9 * max_full
    result = head
    if damaged:
        result = drop_bogus(rebuild(versions))
        if len(result) < max_full:
            # rebuild() join'leri boş satırları sıkıştırabiliyor (2026-10-10 run 38072838863:
            # 358404 < 358406). En uzun tam sürümü taban al, rebuild'deki eksik blokları ekle.
            best = max((drop_bogus(v) for v in versions if v.strip() and not has_bogus_head(v)),
                       key=len)
            result = drop_bogus(merge_missing(best, result))
        if has_bogus_head(result) or bogus_lines(result):
            raise SystemExit(f"{path}: onarılan metinde sahte satır kaldı, yazılmadı")
        if len(result) < max_full:
            raise SystemExit(f"{path}: onarılan metin ({len(result)}) en uzun tam sürümden ({max_full}) kısa")
        for b in blocks(strip_head(head)):
            real = norm(drop_bogus(strip_head(b)))
            if real and real not in norm(result):
                raise SystemExit(f"{path}: HEAD'deki kayıt sonuçta yok, yazılmadı: {b[:80]!r}")
    result = apply_notes(path, result)
    changed = result != head
    if changed and write:
        file.write_text(result, encoding="utf-8")
    return {"path": path, "damaged": damaged, "changed": changed, "head_chars": len(head),
            "result_chars": len(result), "result_lines": result.count("\n"), "max_full": max_full}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="48 hours ago", help="git log --since penceresi")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true", help="yalnız sahte satır kontrolü (CI guard)")
    ap.add_argument("paths", nargs="*", default=ARCHIVES + ["knowledge/lessons.md"])
    a = ap.parse_args()
    if a.check:
        bad = {p: bogus_lines((ROOT / p).read_text(encoding="utf-8")) for p in ARCHIVES}
        bad = {p: v for p, v in bad.items() if v}
        print(json.dumps({"bogus_lines": bad}, ensure_ascii=False))
        return 1 if bad else 0
    report = []
    for p in a.paths:
        if p in ARCHIVES:
            report.append(heal(p, a.since, not a.dry_run))
        else:  # yalnız not ekleme (ör. knowledge/lessons.md)
            f = ROOT / p
            old = f.read_text(encoding="utf-8")
            new = apply_notes(p, old)
            if new != old and not a.dry_run:
                f.write_text(new, encoding="utf-8")
            report.append({"path": p, "changed": new != old, "result_chars": len(new)})
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
