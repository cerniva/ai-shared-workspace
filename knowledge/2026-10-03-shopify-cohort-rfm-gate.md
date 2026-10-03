# COHORT_RFM_GATE

- learned_rule: `COHORT_RFM_GATE`
- learning_id: `learn_e877d8d8b1a1b290`
- sources: `src_d04b5a72ae4029f9` Shopify Help Customers reports; `src_0c0576e57cb62ef8` Admin GraphQL `CustomerRfmGroup`
- checked: 2026-10-03 public pages only. Store admin not opened.
- cohort: default Customer cohort analysis groups by first-order date. Period 0 is returning orders in the same period as the first order. Metrics can be customers, retention rate, gross sales, net sales, or average order value. Projections need 24 months and amount spent per customer.
- RFM: store-only 1-5 quintiles for recency, order count, and amount spent. Group uses R and floor((F+M)/2). Eleven groups include Prospects, who have no orders. Individual digit scores are not shown in admin.
- not_this: a cohort month is not an RFM group. Returning customer rate is not an RFM score. Product Insights Customers is not RFM. Industry percentages are not this store.
- keep: `REPEAT_VALUE_GATE` and `PRODUCT_SALES_SOURCE_GATE`.
