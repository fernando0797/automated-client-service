# Refund Request - Sony PlayStation

## Metadata
```json
{
  "domain": "administrative",
  "subdomain": "refund_request",
  "product": "sony_playstation",
  "type": "cross_doc"
}
```

## Document Purpose
- This cross document is intended for retrieval-augmented support in the **administrative** domain.
- It should be retrieved when the router predicts the current issue belongs to **refund_request** and the product is **sony_playstation**.
- Its goal is to help the response agent produce policy-aware, product-aware answers instead of generic customer-support replies.
- It is written to support triage, summarization, next-step generation, and escalation decisions.

## Overview
- This document covers refund requests involving Sony PlayStation, with special emphasis on PlayStation Store digital content and related policy conditions.
- The PlayStation ecosystem includes hardware, subscriptions, pre-orders, add-ons, in-game consumables, and other digital goods, so refund support must classify the purchase type before anything else.
- Sony publishes formal PlayStation Store cancellation/refund policy pages that are highly specific about timing and download/streaming status.

## Typical Customer Intent
- The customer usually wants one or more of the following:
  - a clear explanation of what policy applies,
  - immediate next steps,
  - confirmation of whether the request is still possible,
  - a refund / cancellation / access recovery / billing correction path,
  - reassurance that the case is understood and being routed correctly.
- The agent should identify whether the customer is asking for information, action, exception handling, or escalation.

## Common Scenarios
- Customer wants a refund for a game purchased on PlayStation Store.
- Customer wants to cancel a pre-order.
- Customer bought downloadable content and changed their mind.
- Customer asks for refund on a subscription or season pass.
- Customer asks for refund after content has started downloading.
- Customer refers to a PlayStation console issue but is actually asking about a digital-store purchase.

## Core Policy Rules
- PlayStation Store digital-purchase handling is policy-driven and product-type specific.
- Sony states that many digital-content purchases can be cancelled within 14 days only if the content has not started downloading or streaming, subject to the relevant category rule.
- Pre-orders can typically be refunded before release, with additional conditions when purchased shortly before release and once the release date has passed.
- In-game consumables delivered immediately are generally not cancellable unless faulty under the cited PlayStation policy wording.
- Season passes and bundles also have specific conditions tied to whether included content has started downloading or streaming.

## Diagnostic Questions To Ask Or Infer
- Is this refund request for a game, DLC, subscription, season pass, pre-order, consumable, or hardware purchase?
- Was the content downloaded, streamed, or otherwise accessed?
- What was the purchase date and, if a pre-order, has the release date passed?
- Was the purchase made on PlayStation Store or through a retailer?

## Resolution Workflow
- 1. Identify exact purchase type and purchase date.
- 2. For PlayStation Store digital content, check whether download or streaming of the main content has started.
- 3. For pre-orders, confirm whether release has occurred and whether the purchase falls within the policy conditions described by Sony.
- 4. For consumables, explain the special limitation where immediate delivery narrows cancellation rights unless faulty.
- 5. If the matter is hardware purchased through a retailer, redirect to retailer/manufacturer physical-goods route rather than PS Store digital policy.

## Product-Specific Notes
- PlayStation refund outcomes frequently depend less on customer intent and more on content state: not downloaded vs downloaded.
- Customers often think 'I never played it much' is the same as 'I never downloaded it'; policy handling requires the latter distinction.
- Pre-order bonus content can complicate entitlement state and should be considered separately where Sony policy references immediately accessible extra content.

## Edge Cases And Failure Modes
- Customer downloaded a pre-order bonus but not the main game.
- Customer requests refund on a bundle where only one component was accessed.
- Customer uses the word PlayStation broadly, but the underlying transaction is in fact a PS Store digital order.

## Escalation Criteria
- Escalate where entitlement/download status is disputed.
- Escalate high-value digital disputes involving bundles, subscriptions, or recurring charges.
- Escalate unauthorized-purchase claims that may involve account-security remediation alongside refund review.

## Response Guidelines For The LLM
- Be precise about content type and download state.
- Use Sony's category logic instead of generic '14-day refund' language for everything.
- Where the purchase is not a PS Store digital transaction, pivot immediately to the correct physical-goods or retailer route.

## What The Agent Should Avoid
- Do not promise outcomes that depend on a seller, region, or account state that has not been verified.
- Do not mix administrative policy handling with technical troubleshooting unless the case clearly spans both.
- Do not assume the product manufacturer controls the refund path when a third-party retailer may own the transaction.
- Do not treat "cancel", "refund", "return", "repair", "charge dispute", and "account recovery" as interchangeable.
- Do not ask the customer to disclose sensitive credentials or security codes.
- Do not cite a physical-goods rule for a digital-content transaction or the reverse.

## Structured Summary Template
- **Problem category:** refund_request
- **Product:** sony_playstation
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
- Sony states that many digital PlayStation Store purchases can be cancelled within 14 days if download/streaming has not started, subject to category-specific conditions.
- Sony states pre-orders can generally be cancelled before release, with additional rules when purchased close to release and after payment is taken.
- Sony's policy pages also state that immediately delivered in-game consumables are generally not cancellable unless faulty.

## Source Notes
- PlayStation Support - How to request a refund for a purchase on PlayStation Store
- PlayStation Legal - PlayStation Store cancellation policy (UK)
- PlayStation Legal - PlayStation Store cancellation policy (US)
- PlayStation Support - How to cancel a PlayStation Store pre-order
- PlayStation Support - PS Store & Refunds

## Example Internal Summary
- The customer is contacting support about **Refund Request - Sony PlayStation**.
- The issue should be treated as an **administrative** workflow rather than as a purely technical troubleshooting case.
- The first task is to classify the transaction or account state correctly.
- The second task is to route the customer to the correct official path and set accurate expectations.
- If policy eligibility is unclear, the response should be cautious and escalation-aware.

## Example Customer-Facing Response
- I can help with that. For PlayStation refund requests, I first need to identify what you bought—game, DLC, subscription, consumable, or pre-order—and whether the content has already started downloading or streaming.
- That matters because PlayStation Store policy is different for each category, and download status is often the deciding factor.

## Authoring Notes
- This document intentionally combines product context with policy/process context.
- It should be updated when official vendor policy materially changes.
- If future retrieval quality drops, add product aliases, region notes, and high-frequency customer phrasings from real tickets.
