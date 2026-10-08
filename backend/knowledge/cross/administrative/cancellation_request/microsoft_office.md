# Cancellation Request - Microsoft Office

## Metadata
```json
{
  "domain": "administrative",
  "subdomain": "cancellation_request",
  "product": "microsoft_office",
  "type": "cross_doc"
}
```

## Document Purpose
- This cross document is intended for retrieval-augmented support in the **administrative** domain.
- It should be retrieved when the router predicts the current issue belongs to **cancellation_request** and the product is **microsoft_office**.
- Its goal is to help the response agent produce policy-aware, product-aware answers instead of generic customer-support replies.
- It is written to support triage, summarization, next-step generation, and escalation decisions.

## Overview
- This document covers cancellation requests for Microsoft Office / Microsoft 365 subscriptions purchased from Microsoft.
- Unlike a physical product, Microsoft Office cancellation is usually subscription-based and tied to the Microsoft account that owns the service.
- The main support objective is to identify the owning account, explain whether cancellation stops future renewal only or also creates refund eligibility, and guide the user through the official Microsoft self-service path whenever possible.

## Typical Customer Intent
- The customer usually wants one or more of the following:
  - a clear explanation of what policy applies,
  - immediate next steps,
  - confirmation of whether the request is still possible,
  - a refund / cancellation / access recovery / billing correction path,
  - reassurance that the case is understood and being routed correctly.
- The agent should identify whether the customer is asking for information, action, exception handling, or escalation.

## Common Scenarios
- Customer wants to stop recurring billing for Microsoft 365.
- Customer no longer needs Family or Personal plan access.
- Customer believes cancellation automatically means refund.
- Customer cannot find the subscription because they are signed into the wrong Microsoft account.
- Customer sees renewal charges and wants the service terminated immediately.
- Customer bought through a third party and expects Microsoft direct cancellation support.

## Core Policy Rules
- Microsoft states cancellation should be done using the same Microsoft account that purchased the subscription.
- Cancelling recurring billing does not automatically guarantee a refund.
- Refund eligibility is case by case and can depend on country/region and purchase circumstances.
- If the subscription was purchased via a third party, store, mobile platform, or partner, the cancellation path may belong to that seller rather than directly to Microsoft.

## Diagnostic Questions To Ask Or Infer
- Was the subscription purchased directly from Microsoft or through another retailer/platform?
- Are you signed into the Microsoft account that owns the subscription?
- Do you want to stop future renewals only, or are you also requesting a refund?
- Is the subscription active, expired, suspended, or showing a billing problem notice?

## Resolution Workflow
- 1. Confirm the exact product and whether it is Microsoft 365 Personal, Family, Basic, or another subscription.
- 2. Send the customer to Services & subscriptions while stressing they must use the purchasing Microsoft account.
- 3. If 'Cancel subscription' appears, instruct them to follow Microsoft's cancellation flow.
- 4. If the goal is also a refund, explain that Microsoft evaluates refund eligibility separately and that cancellation alone does not guarantee reimbursement.
- 5. If the product was bought through a third party, redirect to that seller's billing/cancellation process.

## Product-Specific Notes
- Microsoft Office access is account-centric: being in the wrong Microsoft account is one of the most common reasons customers cannot find or cancel the subscription.
- Service access may continue until the end of the paid billing period if cancellation does not generate a refund.
- Country-specific prorated refund rules may apply in some markets, so support should avoid universal statements unless policy for the relevant market is confirmed.

## Edge Cases And Failure Modes
- Customer confuses removing an app from the device with cancelling the subscription.
- Customer has multiple Microsoft accounts and is signed into the wrong one.
- Customer wants cancellation because of a billing dispute or unrecognized charge, which should be triaged partly as a payment investigation.

## Escalation Criteria
- Escalate when the subscription owner cannot be identified across available Microsoft accounts.
- Escalate if the customer reports unauthorized subscription creation or an unrecognized charge.
- Escalate when the account is inaccessible and the user cannot reach the self-service cancellation page.

## Response Guidelines For The LLM
- Be precise: cancellation, recurring billing off, and refund are not interchangeable.
- Explain the account requirement early to prevent looped troubleshooting.
- Avoid saying 'you will be refunded' unless confirmed by applicable Microsoft path.

## What The Agent Should Avoid
- Do not promise outcomes that depend on a seller, region, or account state that has not been verified.
- Do not mix administrative policy handling with technical troubleshooting unless the case clearly spans both.
- Do not assume the product manufacturer controls the refund path when a third-party retailer may own the transaction.
- Do not treat "cancel", "refund", "return", "repair", "charge dispute", and "account recovery" as interchangeable.
- Do not ask the customer to disclose sensitive credentials or security codes.
- Do not cite a physical-goods rule for a digital-content transaction or the reverse.

## Structured Summary Template
- **Problem category:** cancellation_request
- **Product:** microsoft_office
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
- Microsoft instructs users to sign in with the same Microsoft account used to purchase the subscription when cancelling.
- Microsoft says cancelling recurring billing does not automatically mean a refund.
- Microsoft notes refund eligibility can be assessed case by case and may vary by country/region.

## Source Notes
- Microsoft Support - Cancel your Microsoft subscription
- Microsoft Support - Cancel a Microsoft 365 subscription
- Microsoft Support - How to get a refund on a Microsoft subscription
- Microsoft Support - Microsoft subscription refund policy

## Example Internal Summary
- The customer is contacting support about **Cancellation Request - Microsoft Office**.
- The issue should be treated as an **administrative** workflow rather than as a purely technical troubleshooting case.
- The first task is to classify the transaction or account state correctly.
- The second task is to route the customer to the correct official path and set accurate expectations.
- If policy eligibility is unclear, the response should be cautious and escalation-aware.

## Example Customer-Facing Response
- I can help with that. For Microsoft Office / Microsoft 365, the cancellation has to be done from the same Microsoft account that purchased the subscription.
- Please sign in to Services & subscriptions, choose the plan, and follow the cancellation flow. If you're also requesting money back, note that Microsoft treats refund eligibility separately and cancellation alone does not automatically create a refund.

## Authoring Notes
- This document intentionally combines product context with policy/process context.
- It should be updated when official vendor policy materially changes.
- If future retrieval quality drops, add product aliases, region notes, and high-frequency customer phrasings from real tickets.
