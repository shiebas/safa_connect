# Project Roadmap & TODO

This document tracks the development tasks and their status.

## Feature: Role-Based Dashboards

-   **Objective**: Provide separate, tailored dashboard experiences for National Admin and National Accounts roles.
-   **Tasks**:
    -   **National Admin Dashboard**:
        -   [x] Create a view that shows high-level statistics and pending approvals.
        -   [x] Design a template for the National Admin dashboard.
    -   **National Accounts Dashboard**:
        -   [x] Create a view that focuses on invoice and payment data.
    -   [x] Design a template showing invoice summaries (Paid, Outstanding, Overdue).

## Feature: Member Approval Workflow

-   **Objective**: Implement a multi-step approval process for new members (Players/Officials).
-   **Workflow**:
    1.  Member registers and an invoice is generated.
    2.  Member pays the invoice.
    3.  LFA/Club Admin verifies payment and compliance documents, then gives initial approval.
    4.  National Admin reviews the application and gives final approval.
    5.  Upon final approval, the member becomes `ACTIVE` and is assigned to their club using their `safa_id`.
-   **Tasks**:
    -   [x] **Invoice & Payment**:
        -   [x] Ensure invoice status is correctly updated upon payment.
        -   [x] New player registrations create a `PlayerClubRegistration` with `PENDING` status.
    -   [x] **Initial Approval (LFA/Club)**:
        -   [x] Create an interface for LFA/Club admins to see paid, pending applications.
    -   [x] Add a mechanism to confirm compliance documents are uploaded.
    -   [x] Implement the "Initial Approval" action.
    -   [x] Ensure the National Admin and National Accounts dashboards correctly query for members in all relevant "pending" states (`PENDING`, `PENDING_APPROVAL`).
    -   [x] Refactor `club_admin_add_player` and `club_admin_add_official` views to use lookup forms and link existing members.
    -   [x] Implement `OfficialLookupForm` and refactor `club_admin_add_official` to use it.
    -   [x] Refactor `association_admin_add_official` to use `OfficialLookupForm` and link existing officials to associations.
    -   [x] Verify `approve_player` and `approve_official` views for correct status transitions.
    -   [x] Implement `edit_official` view for updating official information.
    -   [x] Fixed `IndentationError` in `accounts/views.py` related to `edit_official` view.
    -   [x] Fixed `IndentationError` in `accounts/views.py` by removing misplaced code (all occurrences).
    -   [x] **Final Approval (National Admin)**:
        -   [x] Create an interface for National Admins to see members who have initial approval.
        -   [x] Implement the "Final Approval" action.
    -   [x] **Member Activation**:
        -   [x] On final approval, automatically set the member's status to `ACTIVE`.
        -   [x] Ensure the member is correctly associated with their club and visible to the club admin.
    -   [x] Switch to `safa_id` for member identification in URLs, views, and templates.
