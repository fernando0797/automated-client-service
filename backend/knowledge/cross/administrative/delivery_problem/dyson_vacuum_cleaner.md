# Delivery Problem - Dyson Vacuum Cleaner

## Metadata
```json
{
  "domain": "administrative",
  "subdomain": "delivery_problem",
  "product": "dyson_vacuum_cleaner",
  "type": "cross_doc"
}
```

## Document Purpose
- This cross document is intended for retrieval-augmented support in the **administrative** domain.
- It should be retrieved when the router predicts the current issue belongs to **delivery_problem** and the product is **dyson_vacuum_cleaner**.
- Its goal is to help the response agent produce policy-aware, product-aware answers instead of generic customer-support replies.
- It is written to support triage, summarization, next-step generation, and escalation decisions.

## Overview
- This document handles administrative delivery issues for Dyson vacuum-cleaner orders, especially Dyson direct purchases.
- Delivery incidents for large home appliances often require fast classification because a customer may use 'delivery problem' to mean late shipment, failed delivery attempt, damaged-on-arrival product, missing accessories, or a wish to return the order after a delay.
- Dyson's public order and returns materials provide concrete baseline expectations on processing, tracking, and return routes.

## Typical Customer Intent
- The customer usually wants one or more of the following:
  - a clear explanation of what policy applies,
  - immediate next steps,
  - confirmation of whether the request is still possible,
  - a refund / cancellation / access recovery / billing correction path,
  - reassurance that the case is understood and being routed correctly.
- The agent should identify whether the customer is asking for information, action, exception handling, or escalation.

## Common Scenarios
- Customer has not yet received tracking details.
- Tracking exists but has stalled and the vacuum has not arrived.
- Order is delayed beyond the expected processing window.
- Package or machine arrived damaged.
- The wrong Dyson model or missing accessories were delivered.
- Customer wants a full refund because the delayed delivery is no longer useful.

## Core Policy Rules
- Dyson states orders may take one to two business days to process before tracking email is sent.
- Do not treat lack of same-day tracking as automatic shipment failure during the stated processing window.
- If the customer wants to return a Dyson machine purchased direct, Dyson's return policy should be used rather than improvised delivery-only handling.
- Document whether the order was direct from Dyson or from another retailer, because return and delivery control differ.

## Diagnostic Questions To Ask Or Infer
- Was the order purchased directly from Dyson?
- How many business days have passed since the order was placed?
- Have you received the tracking email, and if so, what is the latest scan?
- Was the issue delay, damage, wrong item, or missing components?
- Are you asking for delivery assistance, replacement, or return/refund?

## Resolution Workflow
- 1. Verify order number, purchase channel, and elapsed business days since order placement.
- 2. If within one to two business days and no tracking is available yet, explain Dyson's stated processing window.
- 3. If beyond that stage, use order-status and carrier details to determine whether the case is delayed, lost, or misdelivered.
- 4. For damage or wrong-item cases, gather evidence and route to replacement/return review.
- 5. If the customer now wants to send the machine back, use Dyson's direct returns policy rather than a pure shipment investigation flow.

## Product-Specific Notes
- Vacuum cleaners are bulky physical goods, so failed delivery attempts, packaging damage, and courier handoff problems are relatively common compared with smaller electronics.
- Dyson's direct-sales support pages combine delivery, returns, and contact routes, which makes them useful for blended operational handling.
- If the machine is damaged beyond repair while in Dyson's possession during service, Dyson states replacement may be provided, but this is a service context rather than standard delivery logic.

## Edge Cases And Failure Modes
- Tracking email never arrived, but the order has actually shipped.
- Customer confuses processing delay with carrier delay.
- Customer wants cancellation but the machine is already en route and the better route is return after delivery or refusal according to policy.

## Escalation Criteria
- Escalate if the order exceeds the normal processing window with no tracking or status clarity.
- Escalate delivered-but-not-received or major-damage cases.
- Escalate disputes involving large-value replacements or repeated logistics failures.

## Response Guidelines For The LLM
- Use timeline-based communication: order placed, processing, tracking issued, in transit, delivered.
- Explain that the first one to two business days may still be normal processing according to Dyson.
- Where a return is now preferred, pivot quickly to the return path rather than forcing prolonged tracking-only support.

## What The Agent Should Avoid
- Do not promise outcomes that depend on a seller, region, or account state that has not been verified.
- Do not mix administrative policy handling with technical troubleshooting unless the case clearly spans both.
- Do not assume the product manufacturer controls the refund path when a third-party retailer may own the transaction.
- Do not treat "cancel", "refund", "return", "repair", "charge dispute", and "account recovery" as interchangeable.
- Do not ask the customer to disclose sensitive credentials or security codes.
- Do not cite a physical-goods rule for a digital-content transaction or the reverse.

## Structured Summary Template
- **Problem category:** delivery_problem
- **Product:** dyson_vacuum_cleaner
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
- Dyson says orders may take one to two business days to process before the customer receives tracking information.
- Dyson's returns policy page and product pages describe direct return windows and note that Dyson Direct pays return shipping for covered direct returns in the referenced policy context.
- Dyson support also provides a delivery-and-returns route through its contact/support pages.

## Source Notes
- Dyson - Order Status
- Dyson - Returns Policy
- Dyson - Contact Us / Delivery and returns
- Dyson - Limited Warranty / Repairs and servicing information

## Example Internal Summary
- The customer is contacting support about **Delivery Problem - Dyson Vacuum Cleaner**.
- The issue should be treated as an **administrative** workflow rather than as a purely technical troubleshooting case.
- The first task is to classify the transaction or account state correctly.
- The second task is to route the customer to the correct official path and set accurate expectations.
- If policy eligibility is unclear, the response should be cautious and escalation-aware.

## Example Customer-Facing Response
- I'm sorry your Dyson order hasn't arrived as expected.
- The first thing I need to check is whether the order is still within Dyson's one-to-two-business-day processing window or whether it has moved into a genuine carrier delay. If you share the order number and any tracking details, I can guide the next step—delivery investigation, replacement review, or return path.

## Authoring Notes
- This document intentionally combines product context with policy/process context.
- It should be updated when official vendor policy materially changes.
- If future retrieval quality drops, add product aliases, region notes, and high-frequency customer phrasings from real tickets.
