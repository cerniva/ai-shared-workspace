"""Integrity spec 2026-10-10 rule 6/10: two-process race (HO-20261010-09).

Real OS processes (multiprocessing, spawn) write the same canonical catalog /
ledger at the same time. Every write must survive (no lost update) and the
files must always parse (no torn write). Covers SourceCatalog.add vs
SourceCatalog.add, LearningLedger.add vs LearningLedger.add and
apply_promotions (batch copy-over) vs a concurrent SourceCatalog.add.
"""
from __future__ import annotations

import json
import multiprocessing as mp
import tempfile
import unittest
from pathlib import Path

from scripts.knowledge_bridge import SourceCatalog, source_id
from scripts.learning_bridge import LearningLedger
from scripts.knowledge_promote import apply_promotions

ROUNDS = 20
TIMEOUT = 120


def _source(canonical: str) -> dict:
    return {
        "source_name": "Race fixture", "canonical": canonical, "category": "test",
        "purpose": "Two-process race fixture", "evidence_tier": "official",
        "access_status": "verified-public", "cost_quota": "free",
        "reliability_limits": "Fixture only", "discovered_at": "2026-10-10T00:00:00+00:00",
        "provenance": "verified",
    }


def _learning(sid: str, claim: str) -> dict:
    return {
        "title": "Race", "domain": "race-domain", "claim": claim, "evidence_status": "verified",
        "decision": "RACE_GATE: test.", "outcome": "validated", "next_measurement": "n/a",
        "learned_at": "2026-10-10T00:00:00+00:00", "provenance": "verified", "source_ids": [sid],
        "failure_history": [], "fallback_history": [], "supersedes": None,
    }


def _add_sources(root: str, tag: str, barrier) -> None:
    catalog = SourceCatalog(Path(root) / "knowledge" / "source_catalog.json")
    barrier.wait()
    for i in range(ROUNDS):
        catalog.add(_source(f"https://race.example.com/{tag}/{i}"))


def _add_learnings(root: str, tag: str, barrier) -> None:
    base = Path(root) / "knowledge"
    ledger = LearningLedger(base / "learning_ledger.json", base / "source_catalog.json")
    sid = source_id("https://race.example.com/base")
    barrier.wait()
    for i in range(ROUNDS):
        ledger.add(_learning(sid, f"Race claim {tag} {i}."))


def _promote(root: str, tag: str, barrier) -> None:
    promotions = Path(root) / "knowledge" / "promotions"
    barrier.wait()
    for i in range(ROUNDS):
        doc = {"schema_version": 1, "source": _source(f"https://race.example.com/{tag}/{i}")}
        (promotions / f"{tag}-{i:03d}.json").write_text(json.dumps(doc), encoding="utf-8")
        apply_promotions(Path(root))


class TwoProcessRaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "knowledge" / "promotions").mkdir(parents=True)
        self.catalog = self.root / "knowledge" / "source_catalog.json"
        self.ledger = self.root / "knowledge" / "learning_ledger.json"
        SourceCatalog(self.catalog).add(_source("https://race.example.com/base"))
        self.ctx = mp.get_context("spawn")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def race(self, *jobs) -> None:
        barrier = self.ctx.Barrier(len(jobs))
        procs = [self.ctx.Process(target=fn, args=(str(self.root), tag, barrier)) for fn, tag in jobs]
        for proc in procs:
            proc.start()
        for proc in procs:
            proc.join(TIMEOUT)
            self.assertFalse(proc.is_alive(), "race worker hung (deadlock?)")
            self.assertEqual(proc.exitcode, 0, "race worker crashed")

    def source_ids(self) -> set[str]:
        data = json.loads(self.catalog.read_text(encoding="utf-8"))  # torn write -> ValueError
        return {row["source_id"] for row in data["sources"]}

    def expected(self, *tags: str) -> set[str]:
        ids = {source_id("https://race.example.com/base")}
        for tag in tags:
            ids |= {source_id(f"https://race.example.com/{tag}/{i}") for i in range(ROUNDS)}
        return ids

    def test_two_catalog_writers_lose_nothing(self) -> None:
        self.race((_add_sources, "a"), (_add_sources, "b"))
        self.assertEqual(self.source_ids(), self.expected("a", "b"))
        self.assertEqual(SourceCatalog(self.catalog).validate(), 1 + 2 * ROUNDS)

    def test_two_ledger_writers_lose_nothing(self) -> None:
        self.race((_add_learnings, "a"), (_add_learnings, "b"))
        claims = {row["claim"] for row in json.loads(self.ledger.read_text(encoding="utf-8"))["learnings"]}
        self.assertEqual(claims, {f"Race claim {t} {i}." for t in "ab" for i in range(ROUNDS)})
        self.assertEqual(LearningLedger(self.ledger, self.catalog).validate(), 2 * ROUNDS)

    def test_promote_batch_vs_direct_writer_loses_nothing(self) -> None:
        # Before the canonical lock in apply_promotions, the batch copied its
        # scratch catalog over rows that the other process added meanwhile.
        self.race((_promote, "p"), (_add_sources, "d"))
        self.assertEqual(self.source_ids(), self.expected("p", "d"))
        self.assertEqual(apply_promotions(self.root)["changed_files"], [])

    def test_two_promote_batches_lose_nothing(self) -> None:
        self.race((_promote, "p"), (_promote, "q"))
        self.assertEqual(self.source_ids(), self.expected("p", "q"))


if __name__ == "__main__":
    unittest.main()
