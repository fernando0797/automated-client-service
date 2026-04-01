# Cancellation Request - Fitbit Versa Smartwatch

## Metadata
```json
{
  "domain": "administrative",
  "subdomain": "cancellation_request",
  "product": "fitbit_versa_smartwatch",
  "type": "cross_doc"
}
```

## Document Purpose
- This cross document is intended for retrieval-augmented support in the **administrative** domain.
- It should be retrieved when the router predicts the current issue belongs to **cancellation_request** and the product is **fitbit_versa_smartwatch**.
- Its goal is to help the response agent produce policy-aware, product-aware answers instead of generic customer-support replies.
- It is written to support triage, summarization, next-step generation, and escalation decisions.

## Overview
- This document handles administrative cancellation requests for Fitbit Versa Smartwatch purchases or related order processes.
- Support must distinguish carefully between order cancellation, return after delivery, and warranty/service support. Customers often use the word 'cancel' when they actually mean 'return', 'refund', or 'stop a service'.
- For a physical smartwatch, cancellation is mainly an order-stage issue; after shipment or delivery, the support flow usually changes into return/refund policy handling.

## Typical Customer Intent
- The customer usually wants one or more of the following:
  - a clear explanation of what policy applies,
  - immediate next steps,
  - confirmation of whether the request is still possible,
  - a refund / cancellation / access recovery / billing correction path,
  - reassurance that the case is understood and being routed correctly.
- The agent should identify whether the customer is asking for information, action, exception handling, or escalation.

## Common Scenarios
- Customer wants to cancel before the watch ships.
- Customer placed duplicate orders by mistake.
- Customer changed mind after purchase but before receiving the watch.
- Customer wants to cancel because the expected delivery date changed.
- Customer says the product no longer meets their needs after checkout.
- Customer uses 'cancel' but the item has already been shipped or delivered.

## Core Policy Rules
- Treat cancellation as a pre-shipment or pre-fulfilment request whenever possible.
- If the order is already shipped, do not promise same-day cancellation; explain that the case likely converts into return/refund handling.
- Do not mix device warranty issues with cancellation requests unless the item is already delivered and defective.
- Duplicate-order situations should be triaged quickly because one order may still be interceptable.

## Diagnostic Questions To Ask Or Infer
- Has the order shipped yet?
- Do you have an order number and purchase date?
- Was this bought directly from the manufacturer/store or through a third-party retailer?
- Are you trying to cancel the order itself, or do you want to return the product after delivery?
- Was the reason a duplicate purchase, delivery delay, or change of mind?

## Resolution Workflow
- 1. Check order status immediately: placed, processing, shipped, delivered, or retailer-managed.
- 2. If still unshipped, attempt order cancellation through the order-management flow.
- 3. If already shipped, explain that cancellation may no longer be possible and that return/refund policy will likely apply after receipt.
- 4. For duplicate orders, attempt cancellation on the newer or unintended order first.
- 5. If bought through a third party, redirect the customer to the seller's cancellation/return channel while documenting the reason.

## Product-Specific Notes
- A smartwatch is a physical good, so fulfilment stage matters more than subscription-style cancellation logic.
- If the user also wants to stop Fitbit Premium or another service, that is a separate cancellation stream and should not be conflated with the device order.
- Customers may raise battery, setup, or compatibility concerns during cancellation; if the watch has not shipped, keep the flow administrative rather than technical.

## Edge Cases And Failure Modes
- Customer ordered the wrong model or color and wants to cancel before dispatch.
- Order is in a warehouse handoff state where cancellation is uncertain.
- Gift purchases may involve different payer and recipient identities.

## Escalation Criteria
- Escalate urgent duplicate-order cases where one order is still processing.
- Escalate if payment is captured but the order state is unclear or inconsistent.
- Escalate when the customer disputes that shipment occurred after an attempted cancellation.

## Response Guidelines For The LLM
- Be fast and explicit about the order stage, because that determines whether cancellation is still possible.
- Avoid overpromising reversals after shipment.
- Offer the next best path immediately: cancellation if not shipped, return/refund if already shipped.

## What The Agent Should Avoid
- Do not promise outcomes that depend on a seller, region, or account state that has not been verified.
- Do not mix administrative policy handling with technical troubleshooting unless the case clearly spans both.
- Do not assume the product manufacturer controls the refund path when a third-party retailer may own the transaction.
- Do not treat "cancel", "refund", "return", "repair", "charge dispute", and "account recovery" as interchangeable.
- Do not ask the customer to disclose sensitive credentials or security codes.
- Do not cite a physical-goods rule for a digital-content transaction or the reverse.

## Structured Summary Template
- **Problem category:** cancellation_request
- **Product:** fitbit_versa_smartwatch
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
- For distance sales in the EU, consumers generally have a withdrawal period after receiving eligible goods, which is distinct from a pre-shipment cancellation request.
- Operationally, online retailers usually treat shipped orders differently from unfulfilled orders because fulfilment handoff can make same-order cancellation unavailable.

## Source Notes
- General external-ecommerce operational practice used to distinguish order cancellation from returns for shipped physical goods
- EU consumer-rights framing for distance sales (cooling-off logic for physical goods after receipt)

## Example Internal Summary
- The customer is contacting support about **Cancellation Request - Fitbit Versa Smartwatch**.
- The issue should be treated as an **administrative** workflow rather than as a purely technical troubleshooting case.
- The first task is to classify the transaction or account state correctly.
- The second task is to route the customer to the correct official path and set accurate expectations.
- If policy eligibility is unclear, the response should be cautious and escalation-aware.

## Example Customer-Facing Response
- Thanks for the request. I can help, but the key question is whether your Fitbit Versa order has already shipped.
- If the order is still processing, we should try to cancel it immediately. If it has already shipped, the case usually moves into the return/refund path instead of a pure cancellation flow.

## Authoring Notes
- This document intentionally combines product context with policy/process context.
- It should be updated when official vendor policy materially changes.
- If future retrieval quality drops, add product aliases, region notes, and high-frequency customer phrasings from real tickets.
