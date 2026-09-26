# CORE-04 payment + product audit — 2026-09-26

## Payment read

Source: connected Shopify Admin GraphQL, read-only.

- shop: Mağazam (`i19cci-4e.myshopify.com`)
- `setupRequired`: false
- `checkoutApiSupported`: false (this is the legacy Checkout API capability; it does **not** by itself prove storefront checkout is disabled)
- `paymentSettings.supportedDigitalWallets`: []
- `shopifyPaymentsAccount`: could not be read because the connected app lacks `read_shopify_payments` / `read_shopify_payments_accounts` scope.

Decision: `payments-unproven` remains a blocker. Do not claim payments are enabled or disabled from the current API evidence. Merchant must verify Shopify Admin → Settings → Payments, or the connector must later gain the required read scope.

## Product read

Connected Shopify Admin product search, read-only:

- Reusable Pet Hair Remover Roller — DRAFT. Current visible variant price range starts at EUR 3.71; no product at exact price 2.99 was found in a store-wide `price:2.99` search. No write needed for the old 2.99 issue at this time. Keep draft.
- Restaurant & Café Operations SOP + Checklist Pack — DRAFT, EUR 17.90.
- Restaurant Food Cost & Menu Pricing Pro – Excel Calculator — DRAFT, EUR 14.90.
- 30-Day Social Media Content Kit for Restaurants & Cafés — DRAFT, EUR 9.90.

Decision: all four remain draft. No publish performed.

## Storefront gate

Existing TinyFish evidence still proves storefront password wall / Opening soon. No duplicate fetch is useful while that wall is unchanged.

Next fetch trigger: after Payments is manually verified and the intended three digital products are ready/published, run TinyFish against the public storefront and each of the three product URLs to verify public reachability, product copy/price, and checkout handoff. Password removal remains last human gate.

PayoutLens untouched.
