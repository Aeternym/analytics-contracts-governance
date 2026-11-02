---
schema_version: 1
contract_type: metric
id: MET-0001
status: review
owner_id: OWNER-0001
approver_ids: []
updated_at: "2026-01-01"
acceptance_criteria: [one_completed_order_counts_once, cancelled_order_counts_zero]
related_contract_ids: [DOMAIN-0001]
dimension_ids: [DIM-0001]
segment_ids: [SEG-0001]
---

# MET-0001: Demonstration completed orders

Counts synthetic completed orders by stable order ID. Cancelled and test orders are excluded.

