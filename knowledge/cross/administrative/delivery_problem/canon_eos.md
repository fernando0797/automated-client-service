# Delivery Problem - Canon EOS

## Metadata
```json
{
  "domain": "administrative",
  "subdomain": "delivery_problem",
  "product": "canon_eos",
  "type": "cross_doc"
}
```

## Document Purpose
- This cross document is intended for retrieval-augmented support in the **administrative** domain.
- It should be retrieved when the router predicts the current issue belongs to **delivery_problem** and the product is **canon_eos**.
- Its goal is to help the response agent produce policy-aware, product-aware answers instead of generic customer-support replies.
- It is written to support triage, summarization, next-step generation, and escalation decisions.

## Overview
- This document addresses administrative delivery issues for Canon EOS orders purchased through Canon's online store or equivalent direct-sales channels.
- Delivery problems should be treated separately from product-defect cases. The first objective is to establish whether the issue is delay, tracking ambiguity, damaged parcel, missing item, wrong item, or return-shipping dispute.
- Canon's order help materials provide shipping and return information that support can use to frame customer expectations without making promises beyond store policy.

## Typical Customer Intent
- The customer usually wants one or more of the following:
  - a clear explanation of what policy applies,
  - immediate next steps,
  - confirmation of whether the request is still possible,
  - a refund / cancellation / access recovery / billing correction path,
  - reassurance that the case is understood and being routed correctly.
- The agent should identify whether the customer is asking for information, action, exception handling, or escalation.

## Common Scenarios
- Tracking has not updated and the camera has not arrived.
- Customer received the wrong Canon EOS item or an incomplete package.
- Package arrived visibly damaged.
- Delivery timing changed and customer no longer wants the order.
- Customer wants to know whether shipping fees are refundable.
- Customer received a defective item and wants shipping/refund clarification.

## Core Policy Rules
- Establish whether the item was bought from Canon direct or from another retailer before quoting process steps.
- Separate delivery issue from defect issue: Canon's return documentation specifically notes different refund treatment for shipping/handling depending on whether merchandise is determined defective.
- Do not promise refund of original shipping and handling when policy says those fees are generally not refunded unless the merchandise is determined defective.
- When the wrong item, missing parts, or shipping damage is reported, preserve packaging photos and carrier evidence if internal process requires it.

## Diagnostic Questions To Ask Or Infer
- Where was the Canon EOS purchased: Canon direct or another retailer?
- What does the tracking page currently show, and when was the last scan?
- Was the parcel late, damaged, missing, incomplete, or incorrect?
- Has the box been opened and is the camera physically intact?
- Is the customer seeking a replacement, refund, or shipment investigation?

## Resolution Workflow
- 1. Verify order number, shipment carrier, and last known tracking event.
- 2. Determine whether the issue is delay, loss, damage, wrong item, or incomplete order.
- 3. For damaged or wrong shipments, request order-safe evidence according to policy (photos, packing list, condition on arrival).
- 4. For defects discovered on arrival, route simultaneously through return/defect determination because Canon notes shipping-fee refund depends on defect status.
- 5. For direct-store returns, remind the customer that original shipping/handling is generally not refunded unless Canon determines the item was defective.

## Product-Specific Notes
- For a camera purchase, delivery issues often have high urgency because of travel, event, or professional use deadlines. Document the deadline clearly.
- Canon's shipping page provides typical shipping methods and charges; however, actual support should use the live order record, not generic transit assumptions.
- High-value camera shipments may merit faster fraud or carrier review than low-value accessories.

## Edge Cases And Failure Modes
- Customer wants cancellation after shipment because of delay; this may become a refused-delivery or return case instead of a pure cancellation.
- Bundle or promotional package arrived with missing accessories.
- Customer ordered for an event and seeks expedited replacement after a carrier exception.

## Escalation Criteria
- Escalate lost high-value shipments and packages marked delivered but not received.
- Escalate damage-on-arrival cases requiring carrier and store coordination.
- Escalate disputes over shipping-fee reimbursement when defect status is contested.

## Response Guidelines For The LLM
- Acknowledge urgency, especially where the camera was purchased for time-sensitive use.
- State clearly whether the case is being treated as carrier investigation, return, or defect handling.
- Avoid immediate blame of either carrier or customer until the shipment record is reviewed.

## What The Agent Should Avoid
- Do not promise outcomes that depend on a seller, region, or account state that has not been verified.
- Do not mix administrative policy handling with technical troubleshooting unless the case clearly spans both.
- Do not assume the product manufacturer controls the refund path when a third-party retailer may own the transaction.
- Do not treat "cancel", "refund", "return", "repair", "charge dispute", and "account recovery" as interchangeable.
- Do not ask the customer to disclose sensitive credentials or security codes.
- Do not cite a physical-goods rule for a digital-content transaction or the reverse.

## Structured Summary Template
- **Problem category:** delivery_problem
- **Product:** canon_eos
- **Customer intent:** clarify from narrative
- **Primary blocker:** identify from account / order / payment / shipment / policy status
- **Required evidence:** order number, account owner, purchase channel, purchase date, tracking, payment state, or entitlement state
- **Likely next step:** choose from self-service route, support action, refund review, cancellation flow, return path, security recovery, or escalation
- **Escalate?:** yes / no with reason

## Retrieval Hints
- High-match keywords should include the exact product name plus synonyms or paraphrases of the administrative problem.
- Strong retrieval clues include phrases about:
  - sign-in, password reset, verification code, registration, wrong account,
  - cancel subscription, recurring billing, renewal, stop auto-renew,
  - failed payment, declined card, unknown charge, update billing details,
  - package delayed, damaged parcel, missing shipment, wrong item delivered,
  - refund, accidental purchase, pre-order cancellation, digital entitlement.
- If the ticket text is ambiguous, this document should be ranked below a more exact cross document but above generic domain-only knowledge.

## External Information Incorporated
- Canon's shipping-and-delivery materials provide standard, expedited, and express shipping references for direct orders.
- Canon's returns page says original shipping and handling fees are generally not refunded unless the merchandise is determined by Canon to be defective.
- Canon notes that certain items may be nonreturnable and that some bundle returns require returning all items together.

## Source Notes
- Canon U.S.A. - Shipping & Delivery
- Canon U.S.A. - Returns & Exchanges
- Canon U.S.A. - Orders & Purchases

## Example Internal Summary
- The customer is contacting support about **Delivery Problem - Canon EOS**.
- The issue should be treated as an **administrative** workflow rather than as a purely technical troubleshooting case.
- The first task is to classify the transaction or account state correctly.
- The second task is to route the customer to the correct official path and set accurate expectations.
- If policy eligibility is unclear, the response should be cautious and escalation-aware.

## Example Customer-Facing Response
- I'm sorry you're dealing with a delivery problem on your Canon EOS order.
- The next step is to confirm whether this is a delay, a damaged package, a wrong item, or a defect-on-arrival case, because the process differs. If this was a direct Canon order, please share the order number and the latest tracking status so we can decide whether to open a shipment investigation or move into return/defect handling.

## Authoring Notes
- This document intentionally combines product context with policy/process context.
- It should be updated when official vendor policy materially changes.
- If future retrieval quality drops, add product aliases, region notes, and high-frequency customer phrasings from real tickets.
