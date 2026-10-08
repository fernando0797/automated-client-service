# Payment Issue - Adobe Photoshop

## Metadata
```json
{
  "domain": "administrative",
  "subdomain": "payment_issue",
  "product": "adobe_photoshop",
  "type": "cross_doc"
}
```

## Document Purpose
- This cross document is intended for retrieval-augmented support in the **administrative** domain.
- It should be retrieved when the router predicts the current issue belongs to **payment_issue** and the product is **adobe_photoshop**.
- Its goal is to help the response agent produce policy-aware, product-aware answers instead of generic customer-support replies.
- It is written to support triage, summarization, next-step generation, and escalation decisions.

## Overview
- This document addresses administrative payment problems related to Adobe Photoshop subscriptions or plans bought through Adobe.
- Because Photoshop is commonly sold as a subscription, payment issues can affect both billing continuity and access continuity. A user may report a billing error, missed payment, charge they do not understand, inability to update card details, or a cancellation dispute tied to billing timing.
- Adobe provides official support guidance for updating payment details, retrying failed payments, and understanding cancellation/refund timing.

## Typical Customer Intent
- The customer usually wants one or more of the following:
  - a clear explanation of what policy applies,
  - immediate next steps,
  - confirmation of whether the request is still possible,
  - a refund / cancellation / access recovery / billing correction path,
  - reassurance that the case is understood and being routed correctly.
- The agent should identify whether the customer is asking for information, action, exception handling, or escalation.

## Common Scenarios
- Monthly or annual Photoshop subscription payment failed.
- Card expired or billing address changed.
- Customer cannot update the payment method in the Adobe account.
- Account access is limited or suspended because payment failed.
- Customer wants to cancel after a failed payment and asks whether charges or fees still apply.
- Customer questions a recent Adobe billing charge tied to renewal or contract terms.

## Core Policy Rules
- Adobe support materials direct customers to manage payment details through the Adobe account payment-management flow.
- Adobe notes that if payment methods fail, subscription access may be suspended until payment is successfully completed.
- Adobe states that for most plans, cancelling within 14 days of the initial purchase results in a full refund.
- Adobe's legal subscription terms note that after that 14-day period, refunds and early-termination consequences depend on plan type and region; support should not generalize beyond the applicable policy wording.
- A failed payment and a cancellation request are related but not identical: first establish whether the customer wants to restore service or terminate it.

## Diagnostic Questions To Ask Or Infer
- Is the issue a declined payment, an unknown charge, inability to edit billing details, or a cancellation-billing question?
- Is the customer on an annual paid monthly plan, annual prepaid plan, or month-to-month plan?
- Was the plan purchased directly from Adobe?
- Does the Adobe account currently show suspended access or a billing alert?
- Has the customer already tried updating card number, expiry date, billing name, or billing address?

## Resolution Workflow
- 1. Confirm the plan type and whether the purchase was direct from Adobe.
- 2. If the goal is to continue using Photoshop, direct the customer to update payment details in the Adobe account.
- 3. If payment failed, advise retrying payment after the card/billing details are corrected and allow for posting delay where Adobe states this may take time.
- 4. If the account is suspended after failed payment, explain that access can be restored once payment succeeds.
- 5. If the customer instead wants out of the plan, explain the distinction between refund-within-14-days and later cancellation consequences under the applicable Adobe terms.
- 6. If the user cannot update the payment method, troubleshoot browser/account constraints and then escalate if the billing page still fails.

## Product-Specific Notes
- Photoshop is often a mission-critical application for customers with active projects, so restoring billing can be more urgent than the monetary dispute itself.
- Customers may perceive a failed payment as a software bug because the app shows account notices rather than payment language first.
- Cardholder-name and billing-address mismatches are especially relevant in corporate-card environments, a case Adobe explicitly references in its billing-help materials.

## Edge Cases And Failure Modes
- Customer wants cancellation because payment failed, but the underlying issue is an annual commitment plan with early-termination implications.
- Customer updated the card but the payment has not yet posted.
- Browser incompatibility prevents editing payment details in account settings.

## Escalation Criteria
- Escalate when the Adobe account page will not allow payment update after standard browser/payment checks.
- Escalate when charges are disputed and cannot be reconciled from the Adobe account order/invoice history.
- Escalate when the account remains suspended after successful payment confirmation window has passed.

## Response Guidelines For The LLM
- Use very explicit branching: continue service vs cancel service.
- Do not promise a full refund unless the timing and plan qualify under the applicable Adobe rule.
- Encourage the customer to verify invoices/orders inside the Adobe account before concluding the charge is erroneous.

## What The Agent Should Avoid
- Do not promise outcomes that depend on a seller, region, or account state that has not been verified.
- Do not mix administrative policy handling with technical troubleshooting unless the case clearly spans both.
- Do not assume the product manufacturer controls the refund path when a third-party retailer may own the transaction.
- Do not treat "cancel", "refund", "return", "repair", "charge dispute", and "account recovery" as interchangeable.
- Do not ask the customer to disclose sensitive credentials or security codes.
- Do not cite a physical-goods rule for a digital-content transaction or the reverse.

## Structured Summary Template
- **Problem category:** payment_issue
- **Product:** adobe_photoshop
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
- Adobe says customers can update card details from the Adobe account billing/payment area.
- Adobe says retrying payment after correcting payment details can restore subscription benefits.
- Adobe notes that if payment methods fail, the subscription may be suspended until payment is received.
- Adobe's subscription terms state that, for most plans, cancelling within 14 days of the initial order gives a full refund.

## Source Notes
- Adobe Help - Update payment information
- Adobe Help - Retry a failed or missed payment
- Adobe Help - Fix a failed or missed payment
- Adobe Help - Can't update your payment method on Adobe account
- Adobe Help - Cancel your Adobe trial or subscription
- Adobe Legal - Subscription and Cancellation Terms

## Example Internal Summary
- The customer is contacting support about **Payment Issue - Adobe Photoshop**.
- The issue should be treated as an **administrative** workflow rather than as a purely technical troubleshooting case.
- The first task is to classify the transaction or account state correctly.
- The second task is to route the customer to the correct official path and set accurate expectations.
- If policy eligibility is unclear, the response should be cautious and escalation-aware.

## Example Customer-Facing Response
- I can help with that. First I need to confirm whether you want to keep using Photoshop and just fix the billing issue, or whether you want to cancel the plan entirely.
- If you want to keep the plan, the next step is to update the payment method in your Adobe account and retry the payment. If you want to cancel, refund eligibility depends on timing and plan type, and Adobe states that most plans are fully refundable only when cancelled within 14 days of the initial purchase.

## Authoring Notes
- This document intentionally combines product context with policy/process context.
- It should be updated when official vendor policy materially changes.
- If future retrieval quality drops, add product aliases, region notes, and high-frequency customer phrasings from real tickets.
