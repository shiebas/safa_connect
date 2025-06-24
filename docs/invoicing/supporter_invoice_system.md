# SAFA Supporter Invoice System Documentation

## Overview

The SAFA Supporter Invoice System provides automated financial management for supporter registrations across all membership tiers. This system automatically generates invoices when supporters register for paid memberships, tracks payment status, and integrates with the broader SAFA financial ecosystem.

This documentation covers the supporter-specific invoice functionality introduced as part of the enhanced supporter registration system.

## Table of Contents

1. [Supporter Membership Types & Pricing](#supporter-membership-types--pricing)
2. [Automatic Invoice Generation](#automatic-invoice-generation)
3. [Invoice Details & Structure](#invoice-details--structure)
4. [Registration Flow Integration](#registration-flow-integration)
5. [Administrative Management](#administrative-management)
6. [Geolocation Integration](#geolocation-integration)
7. [Payment Processing](#payment-processing)
8. [Troubleshooting](#troubleshooting)

## Supporter Membership Types & Pricing

### Individual Memberships
- **Premium Supporter**: R150.00 (Base) + R22.50 (15% VAT) = **R172.50 Total**
  - Exclusive content access
  - Priority booking for events
  - Merchandise discounts
  
- **VIP Supporter**: R300.00 (Base) + R45.00 (15% VAT) = **R345.00 Total**
  - All Premium benefits
  - VIP event access
  - Meet & greet opportunities
  - Priority customer support

### Family Packages
- **Family Basic Package**: R450.00 (Base) + R67.50 (15% VAT) = **R517.50 Total**
  - Premium benefits for up to 4 family members
  - Family event invitations
  - Bulk merchandise discounts
  
- **Family Premium Package**: R900.00 (Base) + R135.00 (15% VAT) = **R1,035.00 Total**  
  - VIP benefits for up to 4 family members
  - Exclusive family events
  - Priority seating allocation
  
- **Family VIP Package**: R1,500.00 (Base) + R225.00 (15% VAT) = **R1,725.00 Total**
  - Ultimate family supporter experience
  - Exclusive family events and hospitality
  - Behind-the-scenes access
  - Personal account manager

## Automatic Invoice Generation

### Trigger Events
Invoices are automatically generated when:
1. A user completes supporter registration
2. Selects a paid membership tier
3. Successfully submits the registration form

### Invoice Number Format
```
SUP-YYYYMMDD-XXXXXX
```
Where:
- `SUP` = Supporter designation
- `YYYYMMDD` = Registration date (e.g., 20250622)
- `XXXXXX` = Zero-padded supporter profile ID (e.g., 000001)

Example: `SUP-20250622-000001`

### System Requirements
- Valid club association (uses favorite club or defaults to first available)
- System administrator account for invoice issuing
- Active supporter profile with membership type selection

## Invoice Details & Structure

### Standard Invoice Fields
```python
{
    'invoice_number': 'SUP-20250622-000001',
    'invoice_type': 'REGISTRATION',
    'amount': 172.50,  # Total including VAT
    'tax_amount': 22.50,  # 15% VAT
    'status': 'PENDING',
    'issue_date': '2025-06-22',
    'due_date': '2025-07-22',  # 30 days from issue
    'club': 'Associated Club Object',
    'issued_by': 'System Administrator',
    'payment_method': 'EFT',
    'notes': 'Supporter registration - Premium Supporter'
}
```

### VAT Calculation
- **VAT Rate**: 15% (South African standard)
- **Calculation**: Base Amount × 0.15
- **Total**: Base Amount + VAT Amount

### Payment Terms
- **Standard Terms**: 30 days from issue date
- **Grace Period**: None (immediate overdue after due date)
- **Late Penalties**: As per SAFA financial policies

## Registration Flow Integration

### Step-by-Step Process

1. **User Authentication**
   - User must be logged in
   - Existing supporter profiles redirect to profile page

2. **Form Submission**
   - User completes registration form
   - Geolocation data captured (optional)
   - Membership type selection (required)

3. **Profile Creation**
   - SupporterProfile object created
   - Location timestamp set if coordinates provided
   - Profile saved to database

4. **Invoice Generation**
   - `create_supporter_invoice()` function called
   - Pricing lookup based on membership type
   - VAT calculation performed
   - Invoice object created and linked

5. **User Notification**
   - Success message displayed with invoice details
   - Payment deadline communicated
   - Profile page redirection

### Error Handling
- **No Club Available**: Falls back to first available club
- **Invoice Creation Failure**: User notified, registration still completes
- **System Member Missing**: Automatically created as needed

## Administrative Management

### Admin Interface Features

#### List View Enhancements
- **has_invoice** column shows invoice status
- **location_city** and **location_province** for geographic insights
- **membership_type** filtering
- **created_at** sorting

#### Detail View Sections
1. **Basic Information**
   - User details, favorite club, membership type
   - Verification status and notes

2. **ID Verification**
   - ID number, document upload, date of birth
   - Address information

3. **Location Information**
   - GPS coordinates (latitude/longitude)
   - Reverse-geocoded location data
   - Location accuracy and timestamp

4. **Card/Invoice Integration**
   - Digital card association
   - Physical card association
   - **Invoice linkage and status**

### Filtering & Search Capabilities
```python
list_filter = [
    'membership_type', 
    'is_verified', 
    'favorite_club', 
    'location_province', 
    'location_country'
]

search_fields = [
    'user__first_name', 
    'user__last_name', 
    'user__email', 
    'id_number', 
    'location_city'
]
```

## Geolocation Integration

### Location Data Capture
When users enable location detection:
- **GPS Coordinates**: Stored with 8 decimal precision
- **Reverse Geocoding**: City, province, country extracted
- **Accuracy Tracking**: GPS accuracy in meters recorded
- **Timestamp**: When location was captured

### Location-Based Features
- **Club Recommendations**: Based on proximity to user location
- **Regional Analytics**: Supporter distribution mapping
- **Localized Content**: Location-specific events and offers

### Privacy Compliance
- **User Consent**: Explicit permission request
- **Data Usage Notice**: Clear explanation of location use
- **Optional Feature**: Users can skip location sharing
- **Clear Controls**: One-click location data clearing

## Payment Processing

### Supported Payment Methods
1. **EFT/Bank Transfer** (Default)
   - Bank details provided in invoice
   - Reference number for payment matching

2. **Credit/Debit Card**
   - Online payment gateway integration
   - Immediate payment confirmation

3. **Cash** (In-person only)
   - Office locations specified
   - Receipt generation required

### Payment Status Tracking
- **PENDING**: Invoice created, payment not received
- **PAID**: Payment received and confirmed
- **OVERDUE**: Payment due date passed
- **CANCELED**: Invoice canceled by administrator
- **REFUNDED**: Payment refunded to supporter

### Automated Notifications
- **Invoice Generation**: Immediate notification with payment details
- **Payment Reminders**: 7 days before due date
- **Overdue Notices**: Day after due date, then weekly
- **Payment Confirmation**: Immediate confirmation when paid

## Troubleshooting

### Common Issues

#### Invoice Not Generated
**Symptoms**: Supporter registration completes but no invoice created
**Causes**:
- No available clubs in system
- System member creation failure
- Database connection issues

**Solutions**:
1. Verify at least one club exists in geography.Club
2. Check system user creation permissions
3. Review error logs for database issues

#### Incorrect Pricing
**Symptoms**: Invoice amount doesn't match expected membership fee
**Causes**:
- MEMBERSHIP_PRICING constant outdated
- VAT calculation error
- Currency conversion issues

**Solutions**:
1. Update MEMBERSHIP_PRICING in supporters/views.py
2. Verify VAT rate (currently 15%)
3. Check decimal precision settings

#### Location Data Missing
**Symptoms**: Supporter profile shows no location despite user enabling GPS
**Causes**:
- Browser permission denied
- GPS unavailable
- Reverse geocoding service failure

**Solutions**:
1. Guide users to enable browser permissions
2. Provide manual address entry option
3. Check BigDataCloud API status

### System Health Checks

#### Daily Monitoring
- Invoice generation success rate
- Payment processing status
- Geographic data quality
- Error log review

#### Weekly Reports
- New supporter registrations by membership type
- Outstanding invoice amounts
- Geographic distribution analysis
- Payment method preference trends

### Support Escalation

#### Level 1: Basic Issues
- User account problems
- Payment clarifications
- Basic navigation help

#### Level 2: Technical Issues
- Invoice generation failures
- Location detection problems
- Form submission errors

#### Level 3: System Issues
- Database connectivity
- Payment gateway problems
- Integration failures

## API Integration Points

### Internal APIs
- **Membership System**: Profile data synchronization
- **Geography System**: Club and location data
- **Invoice System**: Core invoice management
- **Card System**: Digital/physical card integration

### External APIs
- **BigDataCloud**: Reverse geocoding service
- **Payment Gateways**: Credit card processing
- **SMS/Email**: Notification services
- **Banking APIs**: EFT payment verification

## Security Considerations

### Data Protection
- **Personal Information**: Encrypted storage of ID numbers
- **Location Data**: Secure handling of GPS coordinates
- **Payment Data**: PCI DSS compliance requirements
- **File Uploads**: Virus scanning for ID documents

### Access Controls
- **Admin Interface**: Role-based access control
- **API Endpoints**: Authentication required
- **File Access**: Secure URL generation
- **Invoice Data**: Privacy protection measures

## Future Enhancements

### Planned Features
1. **Mobile App Integration**: React Native supporter app
2. **Payment Gateway**: Integrated online payments
3. **Loyalty Program**: Points-based reward system
4. **Social Features**: Supporter community platform
5. **Analytics Dashboard**: Real-time supporter insights

### Technical Improvements
1. **Automated Testing**: Unit tests for invoice generation
2. **Performance Optimization**: Database query optimization
3. **Monitoring**: Real-time system health monitoring
4. **Backup Systems**: Automated data backup procedures

---

**Document Version**: 1.0  
**Last Updated**: June 22, 2025  
**Author**: SAFA Development Team  
**Review Schedule**: Monthly

For technical support, contact: `support@safa.net`  
For documentation updates, contact: `dev-team@safa.net`
