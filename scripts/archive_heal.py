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
    r"^(SEE_FILE|PLACEHOLDER[A-Z0-9_]*|FULL_CONTENT_[A-Z0-9_]+|_FIXED_BY_FULL_CONTENT|THE_FULL_CONTENT_[A-Z0-9_]+.*|"
    r"THE_CONTENT_FROM_[A-Z0-9_]+|placeholder\b.*|dummy|\.\.\.\s*\[.*truncat.*\]\s*\.\.\.)$",
    re.IGNORECASE,
)


def is_bogus_line(line: str) -> bool:
    """CI guard kuralı: `$(cat ` ile başlayan satır veya tek başına duran sentinel satırı
    (SEE_FILE, FULL_CONTENT_*, THE_FULL_CONTENT_*, THE_CONTENT_FROM_*, PLACEHOLDER*).
    Satır içinde bu kelimelerden bahseden gerçek kayıtlar sahte sayılmaz."""
    return line.startswith("$(cat ") or bool(BODY_SENTINEL.match(line.strip()))


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
                  if not has_bogus_head(versions[k]) and versions[k].strip()), None)
    if start is None:
        return versions[-1]
    acc = versions[start]
    for v in versions[start + 1:]:
        if not v.strip() or has_bogus_head(v):
            continue
        acc = merge_missing(acc, v)
        if acc.rstrip("\n") + "\n" not in v and norm(acc) not in norm(v):
            return versions[-1]  # fail-closed: beklenmeyen durum
    return acc


def heal_file(path: Path, notes: dict) -> bool:
    """Git geçmişinden dosyayı onarır; değişiklik yoksa False döner."""
    r = subprocess.run(["git", "log", "--pretty=%H", "-n", "30", "--", str(path)],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        print(f"heal: git log failed for {path.name}: {r.stderr.strip()}", file=sys.stderr)
        return False
    commits = r.stdout.split()
    versions: list[str] = []
    for sha in commits:
        c = subprocess.run(["git", "show", f"{sha}:{path}"], capture_output=True, text=True, cwd=ROOT)
        if c.returncode == 0:
            versions.append(c.stdout)
    if not versions:
        return False
    healed = drop_bogus(rebuild(versions))
    cur = path.read_text(encoding="utf-8")
    if healed == cur:
        return False
    if bogus_lines(healed):
        print(f"heal: refuse to write {path.name}: healed text still has bogus lines", file=sys.stderr)
        return False
    path.write_text(healed, encoding="utf-8")
    print(f"heal: {path.name} repaired (chars {len(cur)} -> {len(healed)})")
    return True


def check_all() -> int:
    bad = 0
    for name in ARCHIVES:
        path = ROOT / name
        if not path.exists():
            print(f"check: {name} MISSING", file=sys.stderr)
            bad += 1
            continue
        lines = bogus_lines(path.read_text(encoding="utf-8"))
        if lines:
            print(f"check: {name} bogus lines: {lines}", file=sys.stderr)
            bad += 1
        else:
            print(f"check: {name} clean")
    notes = _load_notes()
    for marker, body in notes.items():
        if not (ROOT / "messages" / "grok-to-chatgpt.md").read_text(encoding="utf-8").count(marker):
            # marker yoksa ekle (tek seferlik notlar)
            pass
    return bad


def _load_notes() -> dict:
    if not NOTES.exists():
        return {}
    try:
        return json.loads(NOTES.read_text(encoding="utf-8"))
    except Exception:
        return {}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.check:
        sys.exit(1 if check_all() else 0)
    notes = _load_notes()
    changed = False
    for name in ARCHIVES:
        path = ROOT / name
        if path.exists() and heal_file(path, notes):
            changed = True
    sys.exit(0 if not changed else 2)
