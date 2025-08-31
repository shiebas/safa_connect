# Pending Work Items

This document tracks ongoing and future development tasks.

## Current Focus: Payment Confirmation & Workflow Progression

### 1. Implement "Confirm Payment" Form/Functionality
- **Description:** Create a new view and form for finance department (National Admin/Accounts, Superuser) to confirm payments.
- **Details:**
    - Allow searching by payment reference (e.g., `MEM XXXXXXXXX/WH12Q`).
    - Upon confirmation, update the `RegistrationWorkflow` to the next appropriate step.
    - Consider creating `Payment` records.
- **Status:** To be implemented.

### 2. Amend Member Registration (`user_registration`) for Supporters
- **Description:** Modify the registration process for "Member" (supporter) role.
- **Details:**
    - Default organization type for supporters: `National Federation`.
    - Hide `province`, `region`, `lfa`, `club`, `association` dropdowns for supporters.
    - Remove `club` as a general requirement for all registration types.
    - Ensure new SAFA ID is generated for supporters.
- **Status:** To be implemented.

### 3. Refine Workflow Progression Logic
- **Description:** Ensure `completion_percentage` is accurate and workflow steps are correctly managed.
- **Details:**
    - `completion_percentage` should reflect actual progress, including payment confirmation.
    - Player/official only available under club/region menus when payment confirmed AND workflow 100% complete.
    - Investigate current 0% completion issue.
    - Consider commands for production environment to manage workflow at intervals.
- **Status:** To be implemented.

## Deferred/Minor Issues

### 1. Duplicated Success Messages on Member Approvals Page
- **Description:** "Player [Name] updated successfully" message appears 3 times after editing a member and redirecting to the approvals page.
- **Current Understanding:** Backend adds message once, but frontend seems to render it multiple times, possibly due to multiple page loads or a browser caching issue.
- **Status:** Deferred for now, focusing on core payment/workflow functionality. Will revisit if it impacts user experience significantly.

---
