# Payment Issue - Microsoft Office

## Metadata
```json
{
  "domain": "administrative",
  "subdomain": "payment_issue",
  "product": "microsoft_office",
  "type": "cross_doc"
}
```

## Document Purpose
- This cross document is intended for retrieval-augmented support in the **administrative** domain.
- It should be retrieved when the router predicts the current issue belongs to **payment_issue** and the product is **microsoft_office**.
- Its goal is to help the response agent produce policy-aware, product-aware answers instead of generic customer-support replies.
- It is written to support triage, summarization, next-step generation, and escalation decisions.

## Overview
- This document handles billing and payment issues related to Microsoft Office / Microsoft 365 subscriptions or purchases.
- Payment incidents can include declined cards, inability to change the payment method, account notices caused by subscription billing problems, and charges the customer does not recognize.
- Microsoft provides official support content for payment-option troubleshooting, billing-charge investigation, subscription problem notices, cancellation, and refund policy framing.

## Typical Customer Intent
- The customer usually wants one or more of the following:
  - a clear explanation of what policy applies,
  - immediate next steps,
  - confirmation of whether the request is still possible,
  - a refund / cancellation / access recovery / billing correction path,
  - reassurance that the case is understood and being routed correctly.
- The agent should identify whether the customer is asking for information, action, exception handling, or escalation.

## Common Scenarios
- Customer's card is declined for Microsoft 365 renewal.
- Customer cannot update the payment method on the Microsoft account.
- Office apps show an account notice because the subscription has a billing problem.
- Customer does not recognize a Microsoft charge.
- Customer believes cancelling the subscription will automatically refund the recent charge.
- Customer has the wrong Microsoft account and cannot see the active subscription.

## Core Policy Rules
- The payment issue must be worked from the Microsoft account that owns the subscription or purchase.
- Microsoft's payment-option troubleshooting includes checking bank restrictions, account setup, and payment-method details rather than assuming a platform error.
- Microsoft provides a specific 'Investigate' route for unrecognized charges.
- Cancelling recurring billing does not automatically create a refund; refund eligibility is separate and case dependent.

## Diagnostic Questions To Ask Or Infer
- Is the issue a declined renewal, inability to change payment method, unknown charge, or Office app billing warning?
- Are you signed into the Microsoft account that purchased the subscription?
- Was the purchase direct from Microsoft or through another retailer/platform?
- Are you seeing an in-app account notice in Word, Excel, or another Office app?
- Did the bank decline the payment or is Microsoft rejecting the method update?

## Resolution Workflow
- 1. Confirm the product and the owning Microsoft account.
- 2. For declined renewals, review the payment method and retry after correction using Microsoft's billing tools.
- 3. For method-update problems, use Microsoft's payment-option troubleshooting route and verify region/card compatibility if relevant.
- 4. If Office apps show an account notice, connect the symptom to the subscription billing issue rather than app corruption.
- 5. For unknown charges, use Microsoft's Manage payments / Investigate workflow.
- 6. If the customer wants to stop further charges, guide cancellation separately from charge investigation and refund review.

## Product-Specific Notes
- Office customers often first notice the problem in an app banner rather than in the billing dashboard.
- Multiple Microsoft accounts are a common root cause of apparent billing confusion.
- A previously declined charge or recurring-billing renewal can be perceived as fraudulent if the customer has forgotten renewal settings.

## Edge Cases And Failure Modes
- Customer attempts to update a card from a different country/region than the Microsoft account context.
- A family member or another authorized user created the charge on a shared payment method.
- The subscription is suspended and the customer thinks reinstalling Office will fix it.

## Escalation Criteria
- Escalate unresolved payment-method update failures after standard billing checks.
- Escalate disputed charges where the Microsoft account owner cannot be conclusively identified.
- Escalate app-access cases where billing is restored but the Office account notice remains after reasonable propagation time.

## Response Guidelines For The LLM
- Translate app symptoms into billing language clearly.
- Differentiate unknown-charge investigation, payment-method update, cancellation, and refund.
- Avoid telling the customer the bank is definitely at fault unless Microsoft's flow supports that conclusion.

## What The Agent Should Avoid
- Do not promise outcomes that depend on a seller, region, or account state that has not been verified.
- Do not mix administrative policy handling with technical troubleshooting unless the case clearly spans both.
- Do not assume the product manufacturer controls the refund path when a third-party retailer may own the transaction.
- Do not treat "cancel", "refund", "return", "repair", "charge dispute", and "account recovery" as interchangeable.
- Do not ask the customer to disclose sensitive credentials or security codes.
- Do not cite a physical-goods rule for a digital-content transaction or the reverse.

## Structured Summary Template
- **Problem category:** payment_issue
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
- Microsoft provides guidance for changing payment methods and troubleshooting payment-option issues.
- Microsoft provides an Investigate route for unrecognized charges from the billing dashboard.
- Microsoft documents an Office account notice specifically tied to Microsoft 365 subscription problems.
- Microsoft states cancelling recurring billing does not automatically mean a refund.

## Source Notes
- Microsoft Support - Troubleshoot payment option issues
- Microsoft Support - How to investigate a billing charge from Microsoft
- Microsoft Support - We've run into a problem with your Microsoft 365 subscription
- Microsoft Support - Cancel your Microsoft subscription
- Microsoft Support - Microsoft subscription refund policy

## Example Internal Summary
- The customer is contacting support about **Payment Issue - Microsoft Office**.
- The issue should be treated as an **administrative** workflow rather than as a purely technical troubleshooting case.
- The first task is to classify the transaction or account state correctly.
- The second task is to route the customer to the correct official path and set accurate expectations.
- If policy eligibility is unclear, the response should be cautious and escalation-aware.

## Example Customer-Facing Response
- It sounds like this may be a Microsoft 365 billing issue rather than an Office installation issue.
- If you're seeing an account notice inside an Office app, please check the subscription from the Microsoft account that bought it. If the issue is a declined charge or payment-method update, we should fix that first; if the charge looks unfamiliar, Microsoft has an official billing-investigation path for that as well.

## Authoring Notes
- This document intentionally combines product context with policy/process context.
- It should be updated when official vendor policy materially changes.
- If future retrieval quality drops, add product aliases, region notes, and high-frequency customer phrasings from real tickets.
