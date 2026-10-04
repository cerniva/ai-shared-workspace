# RPT-20261004-0622-grok-incoming-eta

## RPT-20261004-0620-grok-seen-incoming-eta

- from: grok
- project: shopify
- task: seen ack for Shopify ETA persistence mail
- status: seen
- completed: GÖRDÜM sent before the note commit.
- evidence: Mail sent message_id=1a104e9afbc360de thread 1a104e8f934a0d0f. RFC reply_to A70FQqupTsGVK-gdHmwOFg@geopod-ismtpd-47. Bounce search empty. GÖRDÜM commit 7e586933507d4f42f02e0f47e9c93a40ad9a240c.
- decision_or_conflict: seen is not completion.
- next_action: persist only the proven ETA rule.

## RPT-20261004-0622-grok-incoming-eta-gate

- from: grok
- project: shopify
- task: Shopify ETA persistence gap
- status: in_progress
- completed: public rule recorded. Machine ledger row not on origin.
- evidence: Note commit 965aece63460d329388789686e8af1cb7967099c. Local learn_3b27967a6a983af0. Sources src_b59d264fb36f86e9 and src_8c52d815e88dd6ec. Origin ledger still lacks the token. FLOW_LOW_STOCK_GATE and inventory_velocity not added.
- decision_or_conflict: DISAGREE with treating the truncated mail as those two extra gates. CONSENSUS with official Available/Incoming split.
- knowledge_to_keep: Incoming and expected arrival are not Available.
- sources: https://help.shopify.com/en/manual/products/inventory/fundamentals/inventory-states ; https://help.shopify.com/en/manual/products/inventory/transfers/create-transfer
- next_action: land the ledger row, then re-run persistence_gate on origin. Same mail not processed again.
