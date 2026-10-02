"""Parse TCMB indicative FX bulletin XML without inventing the bulletin date."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass


@dataclass(frozen=True)
class FxQuote:
    code: str
    unit: int
    forex_buying: float
    forex_selling: float


@dataclass(frozen=True)
class FxBulletin:
    tarih: str
    bulletin_no: str
    quotes: dict[str, FxQuote]

    def quote(self, code: str) -> FxQuote:
        return self.quotes[code]


def parse_bulletin(xml_text: str) -> FxBulletin:
    root = ET.fromstring(xml_text)
    if root.tag != "Tarih_Date":
        raise ValueError(f"unexpected root {root.tag}")
    tarih = root.attrib.get("Tarih", "").strip()
    bulletin_no = root.attrib.get("Bulten_No", "").strip()
    if not tarih or not bulletin_no:
        raise ValueError("bulletin date or number missing")
    quotes: dict[str, FxQuote] = {}
    for node in root.findall("Currency"):
        code = node.attrib.get("CurrencyCode", "").strip()
        if not code:
            continue
        unit = int(node.findtext("Unit") or "0")
        buying = float(node.findtext("ForexBuying") or "nan")
        selling = float(node.findtext("ForexSelling") or "nan")
        if unit <= 0 or buying != buying or selling != selling or selling < buying:
            raise ValueError(f"invalid quote for {code}")
        quotes[code] = FxQuote(code, unit, buying, selling)
    if "USD" not in quotes or "EUR" not in quotes:
        raise ValueError("USD and EUR are required")
    return FxBulletin(tarih, bulletin_no, quotes)


def assert_same_bulletin_day(bulletin: FxBulletin, expected_tarih: str) -> None:
    """Refuse to label a bulletin as another calendar day."""
    if bulletin.tarih != expected_tarih:
        raise ValueError(
            f"bulletin date {bulletin.tarih} != expected {expected_tarih}"
        )
