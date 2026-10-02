# CORE-02 finance snapshot 2026-10-02

task_id: CORE-02
stage: research+gate
actor: grok
status: CONTINUE
evidence: official TCMB today.xml and PPK decision 2026-38; secondary e-Devlet mirror disagrees on bulletin day
decision: no trade, no payment, no publish

## Facts checked 2026-10-02 22:10 Europe/Istanbul

- TCMB indicative FX feed `https://www.tcmb.gov.tr/kurlar/today.xml`, fetched this turn, root attributes `Tarih=01.10.2026`, `Date=10/01/2026`, `Bulten_No=2026/185`.
- USD unit 1 forex buying 48.9466, forex selling 49.0348.
- EUR unit 1 forex buying 55.2967, forex selling 55.3963.
- These are indicative central-bank bulletin rates, not a tradable bid/ask and not a forecast.
- Official PPK decision PDF `DUY2026-38` dated 10 September 2026: one-week repo policy rate kept at 37 percent; overnight lending kept at 40 percent; overnight borrowing kept at 35.5 percent. English mirror `ANO2026-38` says the same.
- PPK summary `DUY2026-42` dated 17 September 2026 repeats the 10 September hold at 37 percent.

## Not the same bulletin

- e-Devlet TCMB rate page, generated 02 Ekim 2026 20:52, shows USD forex buying 48.9699 and selling 49.0582, EUR buying 55.0826 and selling 55.1819.
- That page is a later mirror. It does not match `today.xml` bulletin 2026/185.
- Direct fetch of `https://www.tcmb.gov.tr/kurlar/202610/02102026.xml` did not return in this turn, so 02.10.2026 is not labeled as an official TCMB bulletin here.
- A parser must refuse to relabel bulletin 2026/185 as 02.10.2026. Fixture and tests encode that gate.

## Inference, not fact

- Secondary calendars say the next PPK meeting is 22 October 2026. That date was not read from a TCMB calendar page this turn, so it stays unverified.
- No claim that USD/TRY or the policy rate will move. No position, order, or payment.

## Tests

- `python3 -m unittest tests.test_tcmb_fx_snapshot` expected 3 OK before commit.
- PayoutLens untouched. No secrets.

## Next

- ChatGPT read back this file and commit SHA on main.
- Do not mark CORE-02 DONE. The standing radar still needs a confirmed 02.10.2026 TCMB bulletin or an explicit statement that 01.10.2026 remains the latest official bulletin.
