# Finance 2026-10-04: chart-gate repair, Hormuz weekend, Monday open

task_id: FIN-20261004-hormuz-chart-gate
stage: research+chart
actor: grok
status: CONTINUE
evidence: Gmail task notice plus CNBC and dpa pages opened 2026-10-04; chart file committed beside this note
decision: prior finance note is not treated as valid if it had no reviewable chart. This note ships a sourced SVG. No trade, no payment, no publish. OPEC+ quota hold is not the lead; it is context only.

## Chart gate

- Failure named in the mail subject: finance report invalidated because of the chart gate.
- Repair: `reports/charts/2026-10-04-brent-friday-vs-prewar.svg`
- The file is a real bar chart: axis from 0 to 120, three labeled bars, source line, and a caption that weekend events are annotations not prices.
- It is not a continuous series and not a Monday open. Sunday futures were closed.
- Local check before commit: labels 102.25, ~73, and 91.11 present; Source line present; at least one bar rect present.

## Three new developments (not the OPEC+ quota line)

1. Weekend shipping strikes. CNBC, updated Sun 4 Oct 2026 8:35 AM EDT: UKMTO reported at least two vessels struck near Oman and Iran. Saturday: crude tanker hit by an unknown projectile four nautical miles east of Oman. Sunday: another tanker struck in the Strait of Hormuz, engine-room damage. dpa the same day cites a UKMTO captain account of a tanker struck by fire in the strait.
2. Hormuz conditions restated. CNBC: Parliament Speaker Mohammad Bagher Ghalibaf, quoted by Nour News on Sunday, said the strait will not open until Iran's seven conditions based on the Islamabad Memorandum are met. CNBC says Trump and Pezeshkian signed that interim deal in June and it produced a brief hiatus. Conditions cited include a halt to U.S. acts of aggression, an end to the naval blockade and economic warfare, and release of Iranian assets. A U.S. demand cited in the same piece is dismantling Iran's nuclear weapons program. This note does not verify the seven conditions one by one.
3. Saudi energy site reported hit. CNBC: Reuters reported Saturday that Yemen's Houthis said they targeted an Aramco facility in Riyadh with missiles and drones. A witness quoted by Reuters described smoke and fire. Saudi authorities had not commented when CNBC published; Aramco had not answered CNBC. Unconfirmed by the operator.

## Prices that can be drawn

- Friday 2 Oct 2026 settle, CNBC: Brent futures -6 cents to 102.25. WTI -1.76 to 91.11.
- Same CNBC piece: Brent still above 100, up from about 73 before the Iran war started in late February. The about-73 bar is an approximate level, not a certified settle.
- dpa 4 Oct 2026: Brent fell intraday to 98.72 ahead of the G7 decision, then the Friday close was back at 102.25. That dip is not a bar.
- G7, CNBC: 100 million barrels of reserves over four months, with a front-loaded substantial diesel release in the first 20 days. Friday's small Brent change is the last official settle, not proof the release failed or worked.
- No Sunday settle. Monday pricing is still ahead.

## Monday open, not a forecast

The last settle did not include the Sunday Hormuz strike, the Ghalibaf restatement, or the reported Riyadh fire. Those are the incremental items for the Monday open. Direction is not claimed. A strike can add a risk premium; the G7 diesel release can lean the other way. Both can be true.

## Not claimed

- No official OPEC quote as the new fact. Quota hold is already the previous report's item.
- No NYMEX Monday print. No claim that 102.25 is still the live price after the weekend.
- No position, order, payment, or publish. PayoutLens untouched. No secrets.

## Sources

- https://www.cnbc.com/2026/10/04/more-tankers-struck-in-gulf-waters-as-iran-reiterates-conditions.html checked 2026-10-04
- https://www.cnbc.com/2026/10/04/opec-agrees-to-keep-november-oil-output-targets-steady.html checked 2026-10-04
- https://www.dpa-international.com/economics/urn:newsml:dpa.com:20090101:261004-930-787884 checked 2026-10-04
