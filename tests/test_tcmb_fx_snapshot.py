from __future__ import annotations

import unittest
from pathlib import Path

from projects.finance.tcmb_fx import assert_same_bulletin_day, parse_bulletin

FIXTURE = Path(__file__).parent / "fixtures" / "tcmb_20261001.xml"


class TcmbFxSnapshotTests(unittest.TestCase):
    def test_official_fixture_keeps_bulletin_date(self) -> None:
        bulletin = parse_bulletin(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(bulletin.tarih, "01.10.2026")
        self.assertEqual(bulletin.bulletin_no, "2026/185")
        usd = bulletin.quote("USD")
        eur = bulletin.quote("EUR")
        self.assertEqual(usd.unit, 1)
        self.assertEqual(usd.forex_buying, 48.9466)
        self.assertEqual(usd.forex_selling, 49.0348)
        self.assertEqual(eur.forex_selling, 55.3963)
        assert_same_bulletin_day(bulletin, "01.10.2026")

    def test_refuses_to_relabel_bulletin_as_another_day(self) -> None:
        bulletin = parse_bulletin(FIXTURE.read_text(encoding="utf-8"))
        with self.assertRaises(ValueError):
            assert_same_bulletin_day(bulletin, "02.10.2026")

    def test_rejects_selling_below_buying(self) -> None:
        bad = FIXTURE.read_text(encoding="utf-8").replace("49.0348", "48.0000")
        with self.assertRaises(ValueError):
            parse_bulletin(bad)


if __name__ == "__main__":
    unittest.main()
