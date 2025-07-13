# Junior and Senior Member Separation

This document explains the implementation of separate registration processes for junior and senior members in the SAFA membership system.

## Overview

As per the requirements and POPIA act compliance, junior members (under 18 years old) must be registered by a club administrator who is already a SAFA member. This implementation provides:

1. Separate registration paths for junior and senior members
2. Enforcement that juniors can only be registered by club administrators
3. Automatic transition of junior members to senior members when they turn 18
4. Support for duplicate email addresses to accommodate club administrators registering juniors

## Key Changes

### Models

1. Removed the `unique=True` constraint from the `email` field in the `Member` model to allow duplicate emails
2. Added `registered_by_admin` and `registering_admin` fields to the `Member` model to track who registered a member
3. Added `convert_to_senior()` and `check_for_age_transitions()` methods to the `JuniorMember` model

### Views

1. Updated the `membership_application` view to prevent juniors from registering themselves
2. Created a new `JuniorRegistrationView` specifically for club administrators to register junior members
3. Created a `JuniorRegistrationForm` that includes guardian information fields

### Management Command

Created a management command `check_junior_transitions` that can be scheduled to run daily to:
1. Check for junior members who have turned 18
2. Convert them to senior members
3. Send notification emails about the transition

## How to Use

### For Club Administrators

1. Log in as a club administrator
2. Navigate to `/junior/register/` to register a junior member
3. Fill in all required fields, including guardian information
4. Submit the form to create the junior member record

### For Regular Users

1. Navigate to `/apply/` to register as a member
2. If you are under 18, you will be informed that junior members must be registered by a club administrator
3. If you are 18 or older, you can complete the registration process

### For System Administrators

1. Run the age transition check manually:
   ```
   python manage.py check_junior_transitions
   ```

2. Schedule the command to run daily using cron or a similar scheduler:
   ```
   # Example cron entry to run daily at 1 AM
   0 1 * * * cd /path/to/project && python manage.py check_junior_transitions
   ```

## Technical Details

### Email Duplication

The system now allows duplicate email addresses, which is necessary for club administrators to register junior members using their own email addresses. This is implemented by removing the `unique=True` constraint from the `email` field in the `Member` model.

### Age Transition

When a junior member turns 18, the system will:
1. Convert their record from a `JuniorMember` to a regular `Member`
2. Update their `member_type` from 'JUNIOR' to 'SENIOR'
3. Send a notification email about the transition

This process preserves all their membership data while removing the junior-specific information.

### POPIA Compliance

This implementation ensures compliance with the Protection of Personal Information Act (POPIA) by:
1. Requiring guardian consent for junior members
2. Ensuring juniors are registered by authorized club administrators
3. Collecting only necessary information for junior members
