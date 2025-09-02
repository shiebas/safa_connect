# Hierarchical Approval System - Implementation Guide

## Overview
The SAFA Connect system now implements a hierarchical approval system where each administrative level can only approve organizations at the level below them. This ensures proper governance and control over the football association structure.

## Approval Hierarchy

### 1. **National Admin** → Approves **Provinces**
- **Can only approve**: Provinces (9 provinces in South Africa)
- **Requirements**: Province must be `INACTIVE` and `COMPLIANT`
- **Action**: Changes status to `ACTIVE`
- **Result**: Automatically generates an invoice for the province

### 2. **Province Admin** → Approves **Regions**
- **Can only approve**: Regions within their province
- **Requirements**: Region must be `INACTIVE` and `COMPLIANT`
- **Action**: Changes status to `ACTIVE`
- **Scope**: Limited to regions under their jurisdiction

### 3. **Region Admin** → Approves **LFAs**
- **Can only approve**: Local Football Associations within their region
- **Requirements**: LFA must be `INACTIVE` and `COMPLIANT`
- **Action**: Changes status to `ACTIVE`
- **Scope**: Limited to LFAs under their jurisdiction

### 4. **LFA Admin** → Approves **Clubs**
- **Can only approve**: Clubs within their LFA
- **Requirements**: Club must be `INACTIVE` and `COMPLIANT`
- **Action**: Changes status to `ACTIVE`
- **Scope**: Limited to clubs under their jurisdiction

## Implementation Details

### New Views Added
1. **`approve_region`** - For Province Admins to approve regions
2. **`approve_lfa`** - For Region Admins to approve LFAs
3. **`approve_club`** - For LFA Admins to approve clubs

### Updated Views
1. **`update_organization_status`** - Now restricted to National Admin approving provinces only
2. **Dashboard views** - Updated to show only organizations each admin can approve

### URL Patterns
```python
# Hierarchical approval system
path('approve-region/', views.approve_region, name='approve_region'),
path('approve-lfa/', views.approve_lfa, name='approve_lfa'),
path('approve-club/', views.approve_club, name='approve_club'),
```

## Invoice Generation

### When Provinces Are Approved
- **Trigger**: Province status changes from `INACTIVE` to `ACTIVE`
- **Invoice Type**: `ORGANIZATION_MEMBERSHIP`
- **Fee Structure**: Based on `SAFAFeeStructure` for `PROVINCE` type
- **Season**: Current active season
- **Recipient**: The approved province
- **Visibility**: Shows in both National Admin and Province Admin invoice lists

### Invoice Flow
1. National Admin approves province
2. System checks for active season and fee structure
3. Invoice is automatically generated
4. Invoice appears in province's invoice list
5. Province Admin can view and pay the invoice

## Dashboard Updates

### National Admin Dashboard
- **Shows**: Only provinces that are `INACTIVE` and `COMPLIANT`
- **Action**: Approve button only for provinces
- **Other organizations**: Displayed for information only (no approval actions)

### Provincial Admin Dashboard
- **Shows**: Regions within their province
- **Pending Approvals**: Only regions that are `INACTIVE` and `COMPLIANT`
- **Action**: Approve button for compliant, inactive regions

### Regional Admin Dashboard
- **Shows**: LFAs within their region
- **Pending Approvals**: Only LFAs that are `INACTIVE` and `COMPLIANT`
- **Action**: Approve button for compliant, inactive LFAs

### LFA Admin Dashboard
- **Shows**: Clubs within their LFA
- **Pending Approvals**: Only clubs that are `INACTIVE` and `COMPLIANT`
- **Action**: Approve button for compliant, inactive clubs

## Security Features

### Role-Based Access Control
- Each approval function is protected with `@role_required` decorator
- Admins can only approve organizations within their jurisdiction
- Compliance checks prevent approval of non-compliant organizations

### Data Validation
- Status changes are restricted to valid transitions
- Only `INACTIVE` → `ACTIVE` transitions are allowed
- Compliance status is verified before approval

### Audit Trail
- All approval actions are logged
- Success/error messages provide feedback
- Redirects ensure proper navigation flow

## Usage Examples

### National Admin Approving a Province
1. Navigate to National Admin Dashboard
2. View "Pending Organization Approvals"
3. See only provinces that are `INACTIVE` and `COMPLIANT`
4. Click "Approve Province" button
5. Confirm approval
6. Province status changes to `ACTIVE`
7. Invoice is automatically generated

### Province Admin Approving a Region
1. Navigate to Provincial Admin Dashboard
2. View "Pending Region Approvals"
3. See only regions within their province that are `INACTIVE` and `COMPLIANT`
4. Click "Approve" button
5. Confirm approval
6. Region status changes to `ACTIVE`

## Error Handling

### Common Scenarios
- **Non-compliant organization**: Cannot be approved
- **Wrong jurisdiction**: Admin cannot approve outside their scope
- **Invalid status**: Only `INACTIVE` → `ACTIVE` transitions allowed
- **Missing fee structure**: Warning shown but approval proceeds

### User Feedback
- Clear error messages for failed approvals
- Success messages for successful approvals
- Warning messages for partial successes (e.g., approval succeeded but invoice generation failed)

## Future Enhancements

### Potential Improvements
1. **Bulk Approvals**: Allow multiple organizations to be approved at once
2. **Approval Workflows**: Multi-step approval processes for complex cases
3. **Notification System**: Email/SMS notifications for approval actions
4. **Approval History**: Track all approval actions with timestamps
5. **Conditional Approvals**: Require additional documentation before approval

### Integration Points
1. **Compliance System**: Automatic compliance status updates
2. **Financial System**: Invoice generation and payment tracking
3. **Reporting System**: Approval statistics and analytics
4. **Audit System**: Comprehensive logging and reporting

## Testing

### Test Scenarios
1. **National Admin** approves compliant province → Invoice generated
2. **Province Admin** approves compliant region → Status updated
3. **Region Admin** approves compliant LFA → Status updated
4. **LFA Admin** approves compliant club → Status updated
5. **Non-compliant organizations** cannot be approved
6. **Wrong jurisdiction** approvals are blocked
7. **Invalid status changes** are prevented

### Test Data Requirements
- Organizations in various compliance states
- Organizations in different jurisdictions
- Active and inactive seasons
- Fee structures for different organization types
- Users with different admin roles

## Conclusion

This hierarchical approval system ensures proper governance over the SAFA structure while maintaining security and compliance. Each administrative level has clear responsibilities and limitations, preventing unauthorized approvals and ensuring proper oversight of the football association hierarchy.
