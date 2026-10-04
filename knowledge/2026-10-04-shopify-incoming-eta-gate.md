# INCOMING_ETA_GATE

- learned_rule: `INCOMING_ETA_GATE`
- learning_id: `learn_3b27967a6a983af0`
- sources: `src_b59d264fb36f86e9` Shopify Help inventory states; `src_8c52d815e88dd6ec` Shopify Help create inventory transfer
- checked: 2026-10-04 public pages only. Store admin not opened.
- available: sellable quantity. It excludes Incoming.
- incoming: stock on the way from a transfer, purchase order, or app. Not sellable until received and its state changes to Available.
- eta: expected arrival on a transfer shipment is an editable date. It is not a received quantity and not Available.
- not_this: on-hand, committed, unavailable, FLOW_LOW_STOCK_GATE, inventory_velocity, this store's quantities.
- keep: fail closed if the ledger token or source read-back is missing.
- store_status: unknown until an authorized transfer shipment is read. Gate stays open for store ETA values.
