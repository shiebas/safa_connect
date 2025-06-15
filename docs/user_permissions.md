# User Permissions and API Access Documentation

This document describes the user roles, their permissions, and how API access is controlled in the SAFA system.

## User Roles and Permissions

### 1. Club Admin
- **Can view and edit only their own club's data.**
- **API:** `/geography/api/clubs/` returns only their club.
- **Can manage (view/edit) their own players and members (if implemented).**

### 2. LFA Admin (ADMIN_LOCAL_FED)
- **Can view all clubs in their Local Football Association (LFA).**
- **Cannot add, edit, or delete clubs.**
- **API:** `/geography/api/clubs/` returns only clubs in their LFA.

### 3. Region Admin (ADMIN_REGION)
- **Can view all clubs in their region.**
- **Cannot add, edit, or delete clubs.**
- **API:** `/geography/api/clubs/` returns only clubs in their region.

### 4. Province Admin (ADMIN_PROVINCE)
- **Can view all clubs in their province.**
- **Cannot add, edit, or delete clubs.**
- **API:** `/geography/api/clubs/` returns only clubs in their province.

### 5. National Admin (ADMIN_NATIONAL)
- **Can view all clubs in the country.**
- **Cannot add, edit, or delete clubs.**
- **API:** `/geography/api/clubs/` returns all clubs.

### 6. Supporter
- **Can view and edit only their own supporter profile.**
- **API:** `/supporters/api/supporterprofiles/` returns only their profile.

### 7. Other Users
- **Default:** Can only view public data (read-only access).

## Technical Implementation

- **Custom DRF permissions** are used to enforce these rules in each ViewSet.
- **`get_queryset`** is overridden to filter data by user role and assignment (club, LFA, region, province).
- **`permission_classes`** in each ViewSet restricts write access to the appropriate users.
- **SAFE_METHODS** (GET, HEAD, OPTIONS) are allowed for view-only roles; write methods (POST, PUT, PATCH, DELETE) are restricted.

## Extending Permissions
- To add new roles or change access, update the relevant permission class in the app's `permissions.py`.
- For new models, copy the pattern used in `ClubViewSet` and `SupporterProfileViewSet`.

## Example: ClubViewSet Permissions
- Club admins: full access to their club.
- LFA/Region/Province/National: view-only for their scope.
- All others: no access or view-only as appropriate.

---

For more details or to customize permissions, see the code in each app's `permissions.py` and `views.py`.
