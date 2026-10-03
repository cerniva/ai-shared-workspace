# REPEAT_PURCHASE_GATE

- learned_rule: `REPEAT_PURCHASE_GATE`
- learning_id: `learn_4a9dd0fa5ed48efc`
- sources: `src_d04b5a72ae4029f9` Shopify Help Customers reports; `src_0acc40a4a170ff80` Shopify Help analytics fields
- checked: 2026-10-03 public pages only. Store admin not opened.
- returning: a customer who placed an order and whose order history already includes at least one order.
- returning report: customers with two or more orders. One-time customers report: exactly one order.
- rate: returning customers / customers. Help cites a 20-40% display range for most stores; that is not this store.
- cohort period 0: a second order in the same period as the first order still counts as repeat. A cohort month is not an RFM group.
- lag: customer reports other than New vs returning can omit about the last 12 hours. Customer-report history can include orders outside the selected timeframe.
- not_this: first order, session, traffic, public views, RFM group, Product Insights Customers, industry percentage.
- keep: `REPEAT_VALUE_GATE` and `COHORT_RFM_GATE`.
- store_status: unknown until an authorized admin report is read. Gate stays open.
