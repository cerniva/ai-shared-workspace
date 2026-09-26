# PayoutLens demand loop — 2026-09-26

## Evidence
- Shopify official docs: payout CSV/activity reports expose fees and pending transactions; refunds are normally deducted from the next available payout and original card processing fees are not returned. Multi-currency payouts can add plan/region-dependent fees and refund FX can use the current exchange rate.
- Recent merchant discussions independently describe the same operational pain: batched/delayed payouts make order dates diverge from deposit dates; refunds/fees/chargebacks create a second reconciliation layer; merchants report unexplained gaps between sales and received payouts.
- Stripe official pricing/docs also preserve original processing/currency-conversion costs on refunds and expose dispute/payout fees, reinforcing that "gross sales minus a simple fee" is not a reliable deposit model.

Sources checked 2026-09-26:
- https://help.shopify.com/en/manual/payments/shopify-payments/payouts/view-details
- https://help.shopify.com/en/manual/payments/shopify-payments/payouts/refunds
- https://help.shopify.com/en/manual/payments/shopify-payments/store-currency/supported-payout-currencies
- https://stripe.com/pricing
- Reddit demand signals: r/shopify thread 1mx6nw4; r/shopify_growth thread 1rpto4l; r/shopify thread 1k8xtwe.

## Lesson
The strongest initial wedge is not generic reconciliation and not enterprise accounting integration. It is owner-operated / small multi-channel commerce teams who already export CSVs and need to answer: "Why doesn't the bank deposit equal the sales I expected?" The differentiator should be payout-timing explanations across refunds, fees, disputes and FX rather than bookkeeping replacement.

## Changed decision
Positioning sentence for the beta:
**PayoutLens explains why your Shopify/Stripe/PayPal payouts don't match expected sales—matching payout CSVs to bank deposits and surfacing fees, refunds, disputes, FX and timing differences without replacing your accounting software.**

MVP priority becomes: CSV import/mapping -> bank deposit -> payout match -> variance reason categories -> exportable explanation. De-prioritize broad ledger/accounting features until this wedge produces user evidence.

## Next metric
Primary: early-access CTA conversion rate from qualified landing visits.
Secondary: % of imported payout batches that can be explained to <= 1% unexplained variance without manual adjustment; count of real users who report that the variance explanation saved reconciliation time.

## Distribution constraint
Do not promote inside communities that prohibit solicitation. Use such threads only as research evidence unless community rules explicitly allow product feedback/promotion.
