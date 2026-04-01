# Account Access - Amazon Kindle

## Metadata
```json
{
  "domain": "administrative",
  "subdomain": "account_access",
  "product": "amazon_kindle",
  "type": "cross_doc"
}
```

## Document Purpose
- This cross document is intended for retrieval-augmented support in the **administrative** domain.
- It should be retrieved when the router predicts the current issue belongs to **account_access** and the product is **amazon_kindle**.
- Its goal is to help the response agent produce policy-aware, product-aware answers instead of generic customer-support replies.
- It is written to support triage, summarization, next-step generation, and escalation decisions.

## Overview
- This document handles administrative account-access issues that affect Kindle hardware, Kindle books, and Amazon digital services tied to the customer's Amazon account.
- For Kindle, the account is the primary ownership layer: purchased ebooks, device registration, synchronization, cloud library, family library visibility, and payment-backed digital actions are all linked to the Amazon account rather than to the physical reader alone.
- Because of that, account-access incidents can look like product failures even when the root cause is identity, password, two-step verification, device registration, or account-security review.

## Typical Customer Intent
- The customer usually wants one or more of the following:
  - a clear explanation of what policy applies,
  - immediate next steps,
  - confirmation of whether the request is still possible,
  - a refund / cancellation / access recovery / billing correction path,
  - reassurance that the case is understood and being routed correctly.
- The agent should identify whether the customer is asking for information, action, exception handling, or escalation.

## Common Scenarios
- Customer cannot sign in on a Kindle e-reader after changing password.
- Customer reset credentials but the new password is not accepted on the device.
- Customer has access to amazon.com in browser but not on the Kindle device.
- Two-step verification code is not received or the authenticator route has failed.
- Customer sees books missing after signing into a different Amazon account.
- A second-hand Kindle was purchased and is still linked to a prior account.
- Customer suspects unauthorized access because titles, settings, or payment events changed unexpectedly.
- Device registration or deregistration errors prevent synchronization.

## Core Policy Rules
- Never ask the customer to share their full password in chat or email.
- Identity and ownership should be validated using approved support-safe signals such as the registered email address, last digits or partial billing confirmation if allowed by policy, and device/order context.
- If the customer reports suspicious access, prioritize account security before library restoration or content troubleshooting.
- If two-step verification fails, customers should be guided to Amazon's official account-recovery or backup-verification routes rather than improvised workarounds.
- Where possible, separate account-access support from content-quality issues: missing books after account switching is often not a refund or device defect issue.

## Diagnostic Questions To Ask Or Infer
- Are you unable to sign in on the Kindle device, on the Amazon website, or both?
- Did the issue start after a password reset, email-address change, or enabling two-step verification?
- Do you still have access to the email address or phone number associated with the Amazon account?
- Is the Kindle connected to Wi‑Fi and showing the correct date and time?
- Do you see an error about registration, verification code, suspicious activity, or wrong password?
- Did you recently buy the device used or receive it from another person?

## Resolution Workflow
- 1. Confirm whether the customer is using the same Amazon account used for prior Kindle purchases and registration.
- 2. If credentials are uncertain, route the customer to Amazon Password Assistance rather than repeated guess attempts.
- 3. If two-step verification is blocking access, advise backup methods, trusted-device options, or Amazon account recovery.
- 4. If the customer can sign in on web but not on device, verify connectivity and then re-attempt sign-in after rebooting the Kindle.
- 5. If the Kindle remains tied to the wrong account, guide deregistration and re-registration only after confirming the correct target account.
- 6. If books appear missing, check whether the device is signed into another Amazon account and whether the content exists under Manage Your Content and Devices.
- 7. For suspected compromise, instruct password change first, then review security settings and recent activity.

## Product-Specific Notes
- Kindle content is account-bound, not device-bound. Losing access to the account often looks like losing access to the library.
- Amazon's Manage Your Content and Devices controls both digital content visibility and device registration state.
- Verification-code delays can come from spam filtering, blocked SMS, or outdated phone/email settings.
- A device purchased second-hand may need proper deregistration from the prior owner before clean reassignment.

## Edge Cases And Failure Modes
- Customer changed the Amazon account email and now thinks the old account vanished.
- Child profile or household/family configuration is hiding expected books.
- Customer has multiple Amazon accounts in different regions and purchased content under another marketplace account.
- Code delivery fails because the phone number tied to two-step verification is no longer in service.

## Escalation Criteria
- Escalate immediately if the customer reports unauthorized purchases or security compromise.
- Escalate when identity verification cannot be completed through approved support flow.
- Escalate when account recovery is blocked by failed two-step verification and no backup method exists.
- Escalate when content ownership is disputed across two different Amazon accounts.

## Response Guidelines For The LLM
- Lead with reassurance: account-access issues are common and often recoverable.
- Use clear sequencing rather than long paragraphs: verify account, recover sign-in, restore registration, confirm library.
- Do not overpromise restoration timelines if Amazon account recovery is required.
- When the user is locked out, avoid unnecessary troubleshooting about reading features until sign-in is restored.

## What The Agent Should Avoid
- Do not promise outcomes that depend on a seller, region, or account state that has not been verified.
- Do not mix administrative policy handling with technical troubleshooting unless the case clearly spans both.
- Do not assume the product manufacturer controls the refund path when a third-party retailer may own the transaction.
- Do not treat "cancel", "refund", "return", "repair", "charge dispute", and "account recovery" as interchangeable.
- Do not ask the customer to disclose sensitive credentials or security codes.
- Do not cite a physical-goods rule for a digital-content transaction or the reverse.

## Structured Summary Template
- **Problem category:** account_access
- **Product:** amazon_kindle
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
- Amazon officially provides password assistance through email/phone one-time-password recovery.
- Amazon states two-step verification adds a unique code on top of the password.
- Amazon provides a specific recovery path when two-step verification fails.
- Amazon also exposes device/content/account controls through Manage Your Content and Devices.

## Source Notes
- Amazon Customer Service - Managing Your Device, Content, and Account
- Amazon Customer Service - Reset Your Password
- Amazon Customer Service - Why Can't I Sign into My Account?
- Amazon Customer Service - Amazon Device Registration Help & Troubleshooting
- Amazon Customer Service - What is Two-Step Verification?
- Amazon Customer Service - Recover Your Account after Two-Step Verification Fails

## Example Internal Summary
- The customer is contacting support about **Account Access - Amazon Kindle**.
- The issue should be treated as an **administrative** workflow rather than as a purely technical troubleshooting case.
- The first task is to classify the transaction or account state correctly.
- The second task is to route the customer to the correct official path and set accurate expectations.
- If policy eligibility is unclear, the response should be cautious and escalation-aware.

## Example Customer-Facing Response
- Thanks for reaching out. Because Kindle access depends on the Amazon account used to register the device and own the books, the first step is to recover sign-in on that exact Amazon account.
- Please try Amazon's official password-assistance flow, then sign in again on the Kindle. If two-step verification is blocking you, use a backup method or the official account-recovery route.
- Once access is restored, we can confirm the device registration and your Kindle library under Manage Your Content and Devices.

## Authoring Notes
- This document intentionally combines product context with policy/process context.
- It should be updated when official vendor policy materially changes.
- If future retrieval quality drops, add product aliases, region notes, and high-frequency customer phrasings from real tickets.
