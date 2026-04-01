# Account Access - Amazon Echo

## Metadata
```json
{
  "domain": "administrative",
  "subdomain": "account_access",
  "product": "amazon_echo",
  "type": "cross_doc"
}
```

## Document Purpose
- This cross document is intended for retrieval-augmented support in the **administrative** domain.
- It should be retrieved when the router predicts the current issue belongs to **account_access** and the product is **amazon_echo**.
- Its goal is to help the response agent produce policy-aware, product-aware answers instead of generic customer-support replies.
- It is written to support triage, summarization, next-step generation, and escalation decisions.

## Overview
- This document covers administrative account-access issues for Amazon Echo devices and Alexa-linked services.
- Echo access problems are rarely just speaker problems: the device depends on the customer's Amazon account and Alexa app context for registration, household settings, routines, subscriptions, smart-home integrations, and purchasing permissions.
- For support purposes, the core challenge is restoring secure account access while avoiding unsafe identity handling.

## Typical Customer Intent
- The customer usually wants one or more of the following:
  - a clear explanation of what policy applies,
  - immediate next steps,
  - confirmation of whether the request is still possible,
  - a refund / cancellation / access recovery / billing correction path,
  - reassurance that the case is understood and being routed correctly.
- The agent should identify whether the customer is asking for information, action, exception handling, or escalation.

## Common Scenarios
- Customer cannot sign in to the Alexa app after password or email change.
- Echo appears registered to the wrong Amazon account.
- Household member changed credentials and the device stopped working as expected.
- Two-step verification prevents the customer from completing sign-in.
- Customer suspects someone else linked the Echo to their account or changed settings.
- Voice purchasing or household controls changed unexpectedly after account events.
- Device setup fails because the Amazon account cannot be authenticated.

## Core Policy Rules
- Never collect full passwords or one-time codes in support notes.
- Echo support should verify whether the issue is Amazon-account access, Alexa-app access, or device registration.
- Suspected unauthorized access must be treated as a security incident first, not a setup incident.
- If the account owner cannot access the registered email/phone for verification, use formal recovery pathways only.

## Diagnostic Questions To Ask Or Infer
- Can you sign in to amazon.com, or is the issue only inside the Alexa app?
- Did this start after a password reset, email update, or enabling two-step verification?
- Are you trying to set up a new Echo or regain control of an already configured Echo?
- Do you still have access to the email and phone used on the Amazon account?
- Is the device already visible in the Alexa app under your account?

## Resolution Workflow
- 1. Confirm ownership of the Amazon account tied to the Echo.
- 2. Route web/account sign-in failures through Amazon Password Assistance.
- 3. If two-step verification blocks setup, use Amazon's backup/recovery options.
- 4. If web sign-in works but app sign-in fails, update the Alexa app, sign out/in, and recheck device ownership.
- 5. If the Echo is linked to the wrong account, deregister only after confirming the correct account destination.
- 6. After access is restored, verify household settings, voice purchasing, communications, and linked smart-home services.

## Product-Specific Notes
- Echo functionality is mediated through the Alexa ecosystem, so account restoration often fixes what looks like a hardware problem.
- Wrong-account registration can hide routines, shopping lists, devices, and skills.
- A reused or gifted Echo may need deregistration from the previous owner before clean onboarding.

## Edge Cases And Failure Modes
- Customer is in an Amazon Household and is confusing profile-level access with full-account ownership.
- A shared family device has conflicting expectations about who is the primary owner.
- Device setup is blocked by region/account mismatch or the wrong marketplace account.

## Escalation Criteria
- Escalate suspected compromise, especially if purchases or linked smart-home permissions changed without consent.
- Escalate if the user cannot complete identity recovery using standard Amazon flows.
- Escalate when an ownership dispute exists between two Amazon accounts over the same Echo device.

## Response Guidelines For The LLM
- Keep the customer focused on account restoration first, then device recovery.
- When possible, explain why account access affects routines, linked devices, and subscriptions.
- Use security-first language without sounding alarmist.

## What The Agent Should Avoid
- Do not promise outcomes that depend on a seller, region, or account state that has not been verified.
- Do not mix administrative policy handling with technical troubleshooting unless the case clearly spans both.
- Do not assume the product manufacturer controls the refund path when a third-party retailer may own the transaction.
- Do not treat "cancel", "refund", "return", "repair", "charge dispute", and "account recovery" as interchangeable.
- Do not ask the customer to disclose sensitive credentials or security codes.
- Do not cite a physical-goods rule for a digital-content transaction or the reverse.

## Structured Summary Template
- **Problem category:** account_access
- **Product:** amazon_echo
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
- Amazon documents password recovery and separate recovery flows for failed two-step verification.
- Amazon states that two-step verification uses a password plus a unique code for sign-in security.
- Account/device management is centralized through Amazon device and content/account controls.

## Source Notes
- Amazon Customer Service - Reset Your Password
- Amazon Customer Service - What is Two-Step Verification?
- Amazon Customer Service - Recover Your Account after Two-Step Verification Fails
- Amazon Customer Service - Managing Your Device, Content, and Account

## Example Internal Summary
- The customer is contacting support about **Account Access - Amazon Echo**.
- The issue should be treated as an **administrative** workflow rather than as a purely technical troubleshooting case.
- The first task is to classify the transaction or account state correctly.
- The second task is to route the customer to the correct official path and set accurate expectations.
- If policy eligibility is unclear, the response should be cautious and escalation-aware.

## Example Customer-Facing Response
- It looks like your Echo issue is tied to Amazon account access rather than to the speaker hardware itself.
- Please first recover access to the Amazon account used to register the Echo. Once that sign-in works, we can verify Alexa app access and confirm whether the device needs to be re-linked or re-registered.

## Authoring Notes
- This document intentionally combines product context with policy/process context.
- It should be updated when official vendor policy materially changes.
- If future retrieval quality drops, add product aliases, region notes, and high-frequency customer phrasings from real tickets.
