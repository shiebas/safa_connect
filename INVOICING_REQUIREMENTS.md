# Invoicing System Requirements Discussion Summary

This document summarizes the discussion regarding the invoicing system requirements.

## Primary Goal:
*   Every *approved* member (including individuals and organizational entities like provinces, regions, LFAs, clubs, and associations) must receive an invoice.

## Invoice Item:
*   Primarily "Membership Fees / Season [Year]".
*   Potential for other items in the future.

## Generation:
*   Invoices are generated *after* a member/entity is approved.
*   A member's invoice is allocated against their club.

## Display:
*   SAFA details, including constant bank details, must be displayed on the invoice.

## Types/Responsibility:
*   Different invoice types for juniors/seniors.
*   Junior invoices are the responsibility of the club.

## Capture/Management:
*   Invoices will be captured (managed/edited) by National Accounts and Administrators.

---

## Further Clarification Needed (Follow-up Questions):

1.  **Organizational Invoices:**
    *   Does this mean that *organizations themselves* (Provinces, Regions, LFAs, Clubs, Associations) also receive invoices for their own "membership" or affiliation fees, separate from individual members?
    *   If so, what triggers the invoice generation for these organizations? (e.g., annual renewal, initial registration, etc.)
    *   What is the "membership fee" for these organizations? Is it a fixed amount, or based on size/tier?

2.  **Invoice Recipient for Individuals:**
    *   For individual members (players, officials), who is the *recipient* of the invoice? Is it the individual member themselves, or their associated club (especially for juniors)?
    *   If it's the club for juniors, how is this linked? Does the club receive a consolidated invoice for all its junior members, or individual invoices for each junior member that are "allocated against" the club?

3.  **Invoice Statuses & Payment Tracking:**
    *   You mentioned "captured by National Accounts and Administrators." Does this imply manual marking of invoices as paid?
    *   Will there be partial payments?
    *   Do we need to track payment methods (e.g., bank transfer, cash, online)?

4.  **Invoice Numbering:**
    *   Is there a specific format required for invoice numbers? (e.g., sequential, prefix-based, etc.)

5.  **Integration with existing `Invoice` model:**
    *   You already have an `Invoice` model. How should this new functionality integrate with it? Will we extend it, or use it as is?
    *   The `Invoice.create_member_invoice(member)` call we discussed earlier (which I changed to `Invoice.create_member_invoice(user_to_process)`) implies an existing method. Can you confirm its current functionality and what it expects?

6.  **User Interface for Invoice Management:**
    *   How do National Accounts and Administrators "capture" (manage/edit) these invoices? Will there be a dedicated UI for this, or will it be part of the existing admin interface?
