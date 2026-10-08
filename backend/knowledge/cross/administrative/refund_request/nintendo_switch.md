# Refund Request - Nintendo Switch

## Metadata
```json
{
  "domain": "administrative",
  "subdomain": "refund_request",
  "product": "nintendo_switch",
  "type": "cross_doc"
}
```

## Document Purpose
- This cross document is intended for retrieval-augmented support in the **administrative** domain.
- It should be retrieved when the router predicts the current issue belongs to **refund_request** and the product is **nintendo_switch**.
- Its goal is to help the response agent produce policy-aware, product-aware answers instead of generic customer-support replies.
- It is written to support triage, summarization, next-step generation, and escalation decisions.

## Overview
- This document handles refund requests associated with Nintendo Switch hardware, accessories, and digital purchases in the Nintendo ecosystem.
- The support distinction that matters most is physical versus digital. Switch customers often request a 'refund' when the more appropriate route is hardware repair, warranty service, or retailer return handling.
- Nintendo's support and regional policy materials show that digital-purchase and hardware-defect cases should not be handled identically.

## Typical Customer Intent
- The customer usually wants one or more of the following:
  - a clear explanation of what policy applies,
  - immediate next steps,
  - confirmation of whether the request is still possible,
  - a refund / cancellation / access recovery / billing correction path,
  - reassurance that the case is understood and being routed correctly.
- The agent should identify whether the customer is asking for information, action, exception handling, or escalation.

## Common Scenarios
- Customer wants refund for a Nintendo Switch console bought recently.
- Customer wants refund for a digital game or add-on.
- Customer cites Joy-Con drift and asks for money back instead of repair.
- Customer purchased from a retailer and expects Nintendo direct refund handling.
- Customer ordered the wrong item or changed their mind after purchase.

## Core Policy Rules
- Determine first whether the request concerns hardware, accessories, or digital Nintendo eShop content.
- For hardware issues such as Joy-Con drift, support should consider repair/warranty pathways rather than assuming refund is the primary remedy.
- Nintendo support materials emphasize troubleshooting and service-request setup for hardware issues.
- Regional retailer rights and direct-seller terms may control the refund path for physical consoles purchased outside Nintendo direct channels.

## Diagnostic Questions To Ask Or Infer
- Is this refund request for the console, an accessory, or digital content?
- Where was the Nintendo Switch purchased?
- Is the request based on defect, duplicate order, wrong item, or change of mind?
- Has any troubleshooting or service request already been attempted?
- If the issue is Joy-Con drift, does the customer want repair, replacement, or refund?

## Resolution Workflow
- 1. Identify purchase channel and product type: hardware vs digital.
- 2. If the issue is a hardware defect, review troubleshooting and service options before promising refund outcomes.
- 3. For known Joy-Con drift complaints in relevant regions, explain Nintendo's repair route and regional coverage described by Nintendo.
- 4. If the customer bought from a retailer, redirect to the retailer's return/refund policy where appropriate.
- 5. If the case is digital-content related, do not apply console-hardware logic to the decision.

## Product-Specific Notes
- Nintendo publicly states that, in the EEA, UK, and Switzerland, Joy-Con responsiveness/drift repairs are not charged to consumers regardless of whether the issue results from defect or wear and tear, under the stated current policy wording.
- This makes some refund requests better handled as no-charge repair requests rather than as money-back cases.
- Nintendo also offers structured service-request setup for hardware problems through official support.

## Edge Cases And Failure Modes
- Customer wants refund for a hardware defect that is more efficiently handled by repair.
- Retailer purchase limits Nintendo's direct role in refund handling.
- Customer mixes up a console refund request with an eShop digital-content refund request.

## Escalation Criteria
- Escalate when the customer disputes being redirected to retailer policy for a non-direct purchase.
- Escalate if the defect and refund/warranty route are ambiguous.
- Escalate high-value disputes involving repeated failed repairs or disputed service eligibility.

## Response Guidelines For The LLM
- Avoid jumping straight to 'no refund' or 'yes refund' without clarifying hardware versus digital and seller versus manufacturer.
- Where a repair path is strong and customer-friendly, explain it clearly rather than defensively.
- For Joy-Con drift, mention repair availability in the relevant regions without overstating worldwide uniformity.

## What The Agent Should Avoid
- Do not promise outcomes that depend on a seller, region, or account state that has not been verified.
- Do not mix administrative policy handling with technical troubleshooting unless the case clearly spans both.
- Do not assume the product manufacturer controls the refund path when a third-party retailer may own the transaction.
- Do not treat "cancel", "refund", "return", "repair", "charge dispute", and "account recovery" as interchangeable.
- Do not ask the customer to disclose sensitive credentials or security codes.
- Do not cite a physical-goods rule for a digital-content transaction or the reverse.

## Structured Summary Template
- **Problem category:** refund_request
- **Product:** nintendo_switch
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
- Nintendo says affected Joy-Con drift/responsiveness issues can be repaired without charge in the EEA, UK, and Switzerland under the support policy cited.
- Nintendo offers formal service-request setup for Switch hardware issues through its support system.
- Nintendo warranty/service pages also direct customers to use troubleshooting and official service routes for hardware problems.

## Source Notes
- Nintendo Support - Joy-Con Control Sticks Are Not Responding or Respond Incorrectly
- Nintendo Support - Set Up a Service Request for a Nintendo Product
- Nintendo Support - Warranty and Service Information
- Nintendo Support - Nintendo Repairs FAQ

## Example Internal Summary
- The customer is contacting support about **Refund Request - Nintendo Switch**.
- The issue should be treated as an **administrative** workflow rather than as a purely technical troubleshooting case.
- The first task is to classify the transaction or account state correctly.
- The second task is to route the customer to the correct official path and set accurate expectations.
- If policy eligibility is unclear, the response should be cautious and escalation-aware.

## Example Customer-Facing Response
- I can help, but I first need to check whether your refund request is for the Nintendo Switch console, an accessory, or digital content.
- If the problem is hardware-related—especially something like Joy-Con drift—the best route may be Nintendo's repair/service process rather than an immediate refund decision. If you purchased from a retailer, that store's return policy may also control the refund side.

## Authoring Notes
- This document intentionally combines product context with policy/process context.
- It should be updated when official vendor policy materially changes.
- If future retrieval quality drops, add product aliases, region notes, and high-frequency customer phrasings from real tickets.
