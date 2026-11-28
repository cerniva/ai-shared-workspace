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
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.archive_record_guard import RECORD_ID, assert_record_delimiters, missing_record_delimiters

ARCHIVES = ["messages/grok-to-chatgpt.md", "messages/team-reports.md"]
NOTES = ROOT / "config" / "archive_heal_notes.json"
HEAD_BOGUS = re.compile(
    r"^(SEE_FILE|\$\(cat .*|PLACEHOLDER\S*.*|FULL_CONTENT_PLACEHOLDER.*|"
    r"The full content is too large to inline.*)$"
)


# Gövdeye gömülü tam-satır sentinel'ler (2026-10-12: Grok'un LLM yanıt metni arşive sızdı:
# "[... full content truncated in this example ...]" — guard bunu kaçırıyordu).
# 2026-10-17: RESTORED_FROM_PREVIOUS_COMMIT_<sha>, "test content for size check" ve
# "[... full previous content omitted for brevity ...]" grok-to-chatgpt.md'de kalmıştı (PR #197/#201 kalıbı).
# 2026-10-17 12:56: "[TRUNCATED FOR CALL - full content too large ...]" grok-to-chatgpt.md'yi 34 satıra indirdi (308b76a2/c4741b89); heal bunu tanımadığı için fail-closed kaldı.
# 2026-10-10: FULL_CONTENT_WILL_BE_REPLACED,
# THE_FULL_CONTENT_HERE_IS_TOO_LARGE_TO_PASTE..., THE_CONTENT_FROM_TMP_FILE heal'den sonra geri geldi).
BODY_SENTINEL = re.compile(
    r"^(SEE_FILE|PLACEHOLDER[A-Z0-9_]*|FULL_CONTENT_[A-Z0-9_]+|_FIXED_BY_FULL_CONTENT|THE_FULL_CONTENT_[A-Z0-9_]+.*|"
    r"THE_CONTENT_FROM_[A-Z0-9_]+|_?WILL_FIX|placeholder\b.*|dummy|"
    r"RESTORED_FROM_PREVIOUS_COMMIT_[A-Fa-f0-9]+|test content for size check|"
    r"\[\.\.\. full previous content omitted for brevity.*|"
    r"\.\.\.\s*\[.*truncat.*\]\s*\.\.\.|\[\s*\.\.\.[^\[\]]*truncat[^\[\]]*\]\s*\.?|\[\s*full content\b[^\[\]]*\]\s*\.?|"
    r"\[\s*truncated\b[^\[\]]*\]\s*\.?)$",
    re.IGNORECASE,
)


# 2026-10-17 20:48: GitHub MCP get_file_contents büyük dosyayı kesip satır sonuna
# "[+467706 bytes at .content[1].resource.text]" ekliyor; bot bu kesik okumayı geri yazınca
# grok-to-chatgpt.md 480336 B -> 12674 B (283 satır) oldu (7b08d67f) ve heal fail-closed kaldı.
CONNECTOR_TRUNC = re.compile(r"\s*\[\+\d+ (?:bytes|chars|characters) at \.content\[\d+\][^\[\]]*\]\s*$")


def is_bogus_line(line: str) -> bool:
    """CI guard kuralı: `$(cat ` ile başlayan satır veya tek başına duran sentinel satırı
    (SEE_FILE, FULL_CONTENT_*, THE_FULL_CONTENT_*, THE_CONTENT_FROM_*, PLACEHOLDER*).
    Satır içinde bu kelimelerden bahseden gerçek kayıtlar sahte sayılmaz."""
    return (line.startswith("$(cat ") or bool(BODY_SENTINEL.match(line.strip()))
            or bool(CONNECTOR_TRUNC.search(line)))


def bogus_lines(text: str) -> list[int]:
    return [i + 1 for i, line in enumerate(text.splitlines()) if is_bogus_line(line)]


def drop_bogus(text: str) -> str:
    """Gövdeye gömülü sahte satırları sil (gerçek satırlara dokunmaz). Konektör kesme
    işaretiyle biten satır da eksik olduğundan bütünüyle atılır; tam hali git geçmişinde."""
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
    if i < len(text):
        # Keep a complete record at the divergence point. A shared '---' header
        # can otherwise be trimmed away when the following id line differs.
        # Replaying from the nearest boundary is safe: existing blocks are
        # checked against acc below, and ambiguous duplicates fail closed.
        previous = max(text.rfind("\n---\n", 0, i), text.rfind("\n## ", 0, i))
        i = previous + 1 if previous >= 0 else 0
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



def record_ids(text: str) -> set[str]:
    """Kimlikleri koru; rapor başlıkları da append-only kayıttır."""
    message_ids = re.findall(r"^id:\s*([^\r\n]+)", text, re.MULTILINE)
    report_ids = re.findall(r"^##\s+(RPT-[A-Za-z0-9_-]+)\b", text, re.MULTILINE)
    return set(message_ids) | set(report_ids)


RECORD_START = re.compile(r"^id:\s*(?P<mid>[^\r\n]+)$")
RPT_HEADING = re.compile(r"^##\s+(RPT-[A-Za-z0-9_-]+)\b")


def _norm_segment(lines: list[str]) -> str:
    return " ".join(" ".join(l for l in lines if l.strip() != "---").split())


def drop_truncated_duplicate_records(text: str) -> str:
    """rebuild() kırpılmış ara sürümlerden aynı kaydın yarım kopyasını ekleyebiliyor
    (2026-10-17: MSG-20261014-0125-grok-gördüm-video-shopify yalnız başlığıyla ikinci kez
    geldi, archive-heal 'duplicate record IDs' ile kırmızıya düştü). Aynı id'li sonraki kayıt,
    ilk kaydın içinde tamamen yer alıyorsa (alt küme) silinir. Farklı içerikli gerçek
    tekrarlar silinmez; assert_unique_record_ids yine fail-closed durdurur."""
    lines = text.split("\n")
    starts = []
    paired = True
    for i, line in enumerate(lines):
        m = RECORD_START.match(line)
        if m:
            starts.append((i, m.group("mid").strip()))
            paired = False
            continue
        h = RPT_HEADING.match(line)
        if h:
            rid = h.group(1)
            # Metadata+başlık çifti tek kayıttır (record_id_occurrences ile aynı kural).
            if not paired and starts and starts[-1][1] == rid and 0 < i - starts[-1][0] <= 20:
                paired = True
                continue
            starts.append((i, rid))
            paired = True
    if len(starts) < 2:
        return text
    bounds = {}
    for k, (i, rid) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(lines)
        if k + 1 < len(starts):
            j = end - 1
            while j > i and not lines[j].strip():
                j -= 1
            if j > i and lines[j].strip() == "---":
                end = j
        bounds[k] = (i, end)
    first: dict[str, str] = {}
    drop: set[int] = set()
    for k, (i, rid) in enumerate(starts):
        a, b = bounds[k]
        seg = _norm_segment(lines[a:b])
        if rid not in first:
            first[rid] = seg
        elif seg and seg in first[rid]:
            drop.update(range(a, b))
    if not drop:
        return text
    return "\n".join(l for n, l in enumerate(lines) if n not in drop)


def record_id_occurrences(text: str) -> list[str]:
    """Count one RPT metadata/heading pair as one record, never dedupe content.

    Two metadata IDs or two headings with the same ID remain duplicates.
    A heading pairs only with its immediately preceding metadata ID and
    within twenty lines; a different Markdown heading resets the pairing.
    """
    occurrences: list[str] = []
    last_id: str | None = None
    last_id_line = -100
    paired = False
    for index, line in enumerate(text.splitlines()):
        metadata = re.match(r"^id:\s*([^\r\n]+)", line)
        if metadata:
            last_id = metadata.group(1).strip()
            last_id_line = index
            paired = False
            occurrences.append(last_id)
            continue
        heading = re.match(r"^##\s+(RPT-[A-Za-z0-9_-]+)\b", line)
        if heading:
            report_id = heading.group(1)
            if not paired and last_id == report_id and 0 < index - last_id_line <= 20:
                paired = True
            else:
                occurrences.append(report_id)
            continue
        if line.startswith("## "):
            last_id = None
    return occurrences


def assert_unique_record_ids(text: str, path: str) -> None:
    """Fail closed on repeated records; allow one matching RPT metadata/heading pair."""
    seen: set[str] = set()
    duplicates: set[str] = set()
    for record_id in record_id_occurrences(text):
        if record_id in seen:
            duplicates.add(record_id)
        seen.add(record_id)
    if duplicates:
        sample = ", ".join(sorted(duplicates)[:5])
        raise SystemExit(f"{path}: duplicate record IDs ({len(duplicates)}): {sample}; no write")


def assert_history_ids_preserved(versions: list[str], result: str, path: str) -> None:
    """En uzun dosya kontrolünün kaçırdığı, geçmişteki kimlik kaybında yazmayı durdur.

    Kırpılmış/sahte sürümlerdeki stub id'ler (ör. MSG-20260926-0904) beklenen sayılmaz;
    yalnız uzunluğu en uzun tam sürümün %90'ı ve üzeri olan sürümler sayılır.
    """
    full = [drop_bogus(v) for v in versions if v.strip() and not has_bogus_head(v)]
    if not full:
        return
    max_len = max(len(v) for v in full)
    expected: set[str] = set()
    for version in full:
        if len(version) < 0.9 * max_len:
            continue
        expected.update(record_ids(version))
    missing = expected - record_ids(result)
    if missing:
        sample = ", ".join(sorted(missing)[:5])
        raise SystemExit(f"{path}: historical record IDs missing ({len(missing)}): {sample}; no write")


def delimited_record_ids(text: str) -> set[str]:
    """Önünde `---` ayracı olan kayıt id'leri."""
    lines = text.splitlines()
    out = set()
    for i, line in enumerate(lines):
        m = RECORD_ID.match(line)
        if m and i > 0 and lines[i - 1].strip() == "---":
            out.add(m.group(1))
    return out


def restore_known_delimiters(result: str, versions: list[str]) -> str:
    """rebuild() penceredeki eski bir sürümden başlarsa, sonradan düzeltilmiş `---` ayraçları
    kaybolabiliyor (2026-10-17 13:47: b93549b grok-to-chatgpt.md'yi 34 satıra indirdi; heal,
    1f0dbc8'de geri eklenen MSG-20261014-0125 ayracını kaybedip 39026188674/39026232613'te
    'missing record delimiter' ile fail-closed kaldı). Geçmişte ayraçla görülen id'lere ayracı geri koy;
    hiç ayraçla görülmemiş id'ler fail-closed kalır."""
    missing = missing_record_delimiters(result)
    if not missing:
        return result
    known: set[str] = set()
    for v in versions:
        if v.strip() and not has_bogus_head(v):
            known |= delimited_record_ids(v)
    lines = result.split("\n")
    for ln in reversed(missing):
        m = RECORD_ID.match(lines[ln - 1])
        if m and m.group(1) in known:
            lines.insert(ln - 1, "---")
    return "\n".join(lines)


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
    if damaged:
        result = drop_truncated_duplicate_records(result)
        result = restore_known_delimiters(result, versions)
    assert_unique_record_ids(result, path)
    assert_record_delimiters(result, path)
    assert_history_ids_preserved(versions, result, path)
    changed = result != head
    if changed and write:
        file.write_text(result, encoding="utf-8")
    return {"path": path, "damaged": damaged, "changed": changed, "head_chars": len(head),
            "result_chars": len(result), "result_lines": result.count("\n"), "max_full": max_full}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="14 days ago", help="git log --since penceresi")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true", help="yalnız sahte satır kontrolü (CI guard)")
    ap.add_argument("paths", nargs="*", default=ARCHIVES + ["knowledge/lessons.md"])
    a = ap.parse_args()
    if a.check:
        bad = {p: bogus_lines((ROOT / p).read_text(encoding="utf-8")) for p in ARCHIVES}
        bad = {p: v for p, v in bad.items() if v}
        missing = {p: missing_record_delimiters((ROOT / p).read_text(encoding="utf-8")) for p in ARCHIVES}
        missing = {p: v for p, v in missing.items() if v}
        print(json.dumps({"bogus_lines": bad, "missing_record_delimiters": missing}, ensure_ascii=False))
        return 1 if bad or missing else 0
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
