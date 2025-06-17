# SAFA Digital Card System Implementation Guide

**Version**: 1.0  
**Last Updated**: June 17, 2025  
**Prepared by**: SAFA Development Team

## Table of Contents

1. [Introduction](#introduction)
2. [System Overview](#system-overview)
3. [Technical Architecture](#technical-architecture)
4. [Implementation Steps](#implementation-steps)
   - [4.1 Card Number Generation with Luhn Algorithm](#41-card-number-generation-with-luhn-algorithm)
   - [4.2 Digital Card Design](#42-digital-card-design)
   - [4.3 Google Wallet Integration](#43-google-wallet-integration)
5. [Security Considerations](#security-considerations)
6. [User Guides](#user-guides)
7. [Administrative Functions](#administrative-functions)
8. [Future Enhancements](#future-enhancements)
9. [Troubleshooting](#troubleshooting)
10. [Appendices](#appendices)

## 1. Introduction <a name="introduction"></a>

The SAFA Digital Card System transforms traditional membership cards into secure, feature-rich digital cards that resemble banking cards. This system allows members to carry their membership information on their mobile devices, enables quick verification through QR codes, and integrates with digital wallet platforms.

### 1.1 Purpose

This document provides a comprehensive overview of the implementation process, technical specifications, and usage guidelines for the SAFA Digital Card System. It serves as both a reference document for technical staff and a training resource for administrators.

### 1.2 Scope

The document covers:

- Digital card design and functionality
- Card number generation with Luhn algorithm validation
- Google Wallet integration
- Security protocols
- Administrative processes

## 2. System Overview <a name="system-overview"></a>

### 2.1 Key Features

The SAFA Digital Card System includes:

- **Bank Card-Like Design**: Professional design with visual elements similar to financial cards
- **Luhn Algorithm Validation**: Industry-standard check digit system for card number validation
- **Interactive Elements**: 3D effects, card flip animations, and responsive design
- **Google Wallet Integration**: Digital cards can be added to members' Google Wallet accounts
- **Security Features**: Encrypted QR codes, secure verification system
- **Administrative Dashboard**: Comprehensive management interface for admins

### 2.2 User Roles

- **Members**: End users who receive and use digital cards
- **Administrators**: Staff who manage and monitor the card system
- **Verifiers**: Personnel who validate cards at events using the QR verification system

## 3. Technical Architecture <a name="technical-architecture"></a>

### 3.1 Technology Stack

- **Backend Framework**: Django 3.2+
- **Database**: PostgreSQL (via dj-database-url)
- **Frontend**: HTML5, CSS3, JavaScript (with Bootstrap 5)
- **Card Generation**: Pillow, QRCode
- **Digital Wallet**: Google Wallet API
- **Security**: Django signing, Cryptography library

### 3.2 Database Schema

The digital card system primarily uses the `DigitalCard` model with the following key fields:

```python
class DigitalCard(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    card_number = models.CharField(max_length=16, unique=True)
    card_uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, choices=CARD_STATUS_CHOICES)
    issued_date = models.DateTimeField(auto_now_add=True)
    expires_date = models.DateField()
    qr_code_data = models.TextField(blank=True)
    qr_code_version = models.IntegerField(default=1)
    qr_image = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
```

### 3.3 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/membership-cards/my-card/` | GET | View member's digital card |
| `/membership-cards/qr-code/` | GET | Get QR code data for a card |
| `/membership-cards/verify/` | POST | Verify a scanned QR code |
| `/membership-cards/google-wallet/` | GET | Add card to Google Wallet |
| `/membership-cards/dashboard/` | GET | Admin dashboard for card system |

## 4. Implementation Steps <a name="implementation-steps"></a>

### 4.1 Card Number Generation with Luhn Algorithm <a name="41-card-number-generation-with-luhn-algorithm"></a>

The Luhn algorithm (also known as the "modulus 10" or "mod 10" algorithm) is widely used to validate identification numbers, including credit card numbers. We've implemented this to ensure SAFA card numbers can be validated for authenticity.

#### Algorithm Implementation

```python
def generate_luhn_check_digit(self, partial_number):
    """Generate Luhn algorithm check digit for card validation"""
    # Convert to list of integers
    digits = [int(d) for d in partial_number]
    
    # Double every second digit from right to left
    for i in range(len(digits)-2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
            
    # Sum all digits
    total = sum(digits)
    
    # Calculate check digit (what to add to make multiple of 10)
    check_digit = (10 - (total % 10)) % 10
    
    return str(check_digit)
```

#### Card Number Format

- First digit: "2" (SAFA prefix)
- Next 4 digits: Current year (e.g., 2025)
- Next 10 digits: 9 random digits + 1 Luhn check digit

Example: `2 2025 123456789 0`

### 4.2 Digital Card Design <a name="42-digital-card-design"></a>

The digital card features a modern, professional design inspired by banking cards, including:

#### Front Side Elements
- SAFA logo and branding
- Member name and SAFA ID
- 16-digit card number with proper spacing
- Expiration date in MM/YY format
- Status indicator (Active, Suspended, Expired)
- Chip icon for banking card aesthetic
- Gold accent for premium feel

#### Back Side Elements
- Magnetic strip design
- QR code for verification
- Security text and instructions
- Terms of use information

#### Interactive Features
- 3D tilt effect on desktop devices
- Card flip animation to view front and back
- Touch-friendly design for mobile devices

### 4.3 Google Wallet Integration <a name="43-google-wallet-integration"></a>

The integration with Google Wallet allows members to add their SAFA membership cards to their Google Wallet accounts. This implementation uses Google's Pay API for Passes.

#### Configuration Requirements

1. **Google Cloud Project Setup**:
   - Create a project in Google Cloud Console
   - Enable Google Wallet API
   - Create service account with Wallet Object Issuer permissions
   - Download service account key JSON file

2. **Django Settings Configuration**:
   ```python
   # Google Wallet Settings
   GOOGLE_WALLET_ENABLED = True
   GOOGLE_WALLET_ISSUER_ID = 'your-issuer-id'  
   GOOGLE_WALLET_SERVICE_ACCOUNT_EMAIL = 'service-account@project.iam.gserviceaccount.com'
   GOOGLE_WALLET_KEY_FILE = '/path/to/service-account-key.json'
   ```

#### Implementation Process

1. **Class Definition**: Create a template for how all cards will appear in Google Wallet
2. **Object Creation**: Generate individual passes for each member's card
3. **JWT Generation**: Create a signed JWT token for secure pass addition
4. **User Flow**: Present a clean interface for members to add their cards to Google Wallet

#### Sample Code for Pass Creation

```python
def create_wallet_object(self, issuer_id, class_suffix, digital_card):
    """Create a Google Wallet pass object for a specific member"""
    # Get user from digital card
    user = digital_card.user
    
    # Form full class and object IDs
    class_id = f"{issuer_id}.{class_suffix}"
    object_id = f"{class_id}.{user.safa_id}_{int(time.time())}"
    
    # Create the pass object with member details
    generic_object = {
        'id': object_id,
        'classId': class_id,
        'genericType': 'GENERIC_TYPE_UNSPECIFIED',
        'hexBackgroundColor': '#006633',
        'logo': {
            'sourceUri': {
                'uri': f"{settings.BASE_URL}/static/images/safa_logo_small.png"
            }
        },
        'header': {
            'defaultValue': {
                'language': 'en-US',
                'value': f"{user.get_full_name()}"
            }
        },
        'subheader': {
            'defaultValue': {
                'language': 'en-US',
                'value': f"SAFA ID: {user.safa_id}"
            }
        },
        # Additional fields omitted for brevity
    }
    
    # API call to create the object
    session = self.get_authorized_session()
    response = session.post(self.object_url, json=generic_object)
    # Process response...
```

## 5. Security Considerations <a name="security-considerations"></a>

### 5.1 Card Validation

- **Luhn Algorithm**: Prevents accidental or deliberate errors in card numbers
- **QR Code Encryption**: Card data in QR codes is signed using Django's signing module
- **Version Control**: QR codes include version numbers to invalidate old versions

### 5.2 Authentication and Authorization

- Login required for accessing digital cards
- Staff-only access for administrative functions
- Role-based permissions for different operations

### 5.3 Data Protection

- Sensitive data is not stored in QR codes
- Limited personal information on visible card elements
- Secure API calls for Google Wallet integration

## 6. User Guides <a name="user-guides"></a>

### 6.1 For Members

1. **Accessing Your Digital Card**:
   - Log in to your SAFA account
   - Navigate to "My Card" section
   - View your digital card with all details

2. **Adding Card to Google Wallet**:
   - From your digital card view, click "Add to Google Wallet"
   - Follow the prompts to save the card to your Google Wallet account
   - Access your card anytime from the Google Wallet app

3. **Sharing Your Card**:
   - Use the "Share" button to share your card details
   - Download an image of your card for offline use
   - Present QR code for verification at events

### 6.2 For Verifiers

1. **Verifying a Card**:
   - Use the SAFA verification app or web interface
   - Scan the member's QR code
   - System will display verification status and member details
   - Check the status indicator (Active, Suspended, Expired)

## 7. Administrative Functions <a name="administrative-functions"></a>

### 7.1 Card Management

- **Creating Cards**: Automatically generated when members are approved
- **Revoking Cards**: Change status to "Revoked" for security issues
- **Card Renewal**: Update expiration dates for membership renewals
- **Regenerating QR Codes**: Force regeneration for security purposes

### 7.2 Dashboard Functions

- View overall system statistics
- Monitor card status distributions
- Track Google Wallet integration usage
- Generate reports on card usage

## 8. Future Enhancements <a name="future-enhancements"></a>

### 8.1 Planned Features

- **Apple Wallet Integration**: Extend digital wallet support to iOS devices (see dedicated implementation guide)
- **Payment Integration**: Allow for purchases using membership cards
- **Location Services**: Location-based check-ins at events
- **Multiple Card Designs**: Tiered designs based on membership level
- **NFC Integration**: Enable tap-to-verify functionality

### 8.2 Technical Roadmap

1. **Q3 2025**: Apple Wallet integration
2. **Q4 2025**: Payment processing capabilities
3. **Q1 2026**: NFC verification support
4. **Q2 2026**: Enhanced analytics and reporting

## 9. Troubleshooting <a name="troubleshooting"></a>

### 9.1 Common Issues

#### QR Code Not Scanning
- Ensure adequate lighting
- Verify screen brightness is high enough
- Check that QR code is fully visible
- Regenerate QR code if persistent issues

#### Google Wallet Addition Failing
- Verify Google Wallet is installed on device
- Check internet connectivity
- Ensure Google account is properly set up
- Verify service account credentials are valid

#### Card Not Showing Updated Information
- Clear browser cache
- Force refresh the page
- Check for session timeout issues
- Verify database synchronization

### 9.2 Support Resources

- Technical support: support@safa.org.za
- Developer documentation: [Internal Developer Wiki]
- API documentation: [API Documentation Link]

## 10. Appendices <a name="appendices"></a>

### 10.1 Required Packages

```
# Core requirements
Django>=3.2.0,<4.0.0
djangorestframework>=3.12.0,<4.0.0
pillow>=8.0.0,<10.0.0
dj-database-url>=0.5.0
psycopg2-binary>=2.9.0
gunicorn>=20.0.0

# Google Wallet integration
google-auth>=2.10.0
google-api-python-client>=2.50.0
google-auth-oauthlib>=1.0.0

# QR Code generation
qrcode>=7.0.0
pillow>=8.0.0
```

### 10.2 Glossary

- **Luhn Algorithm**: A checksum formula used to validate identification numbers
- **QR Code**: Quick Response code that stores data in a machine-readable optical label
- **Google Wallet**: Digital wallet platform developed by Google
- **JWT**: JSON Web Token, a compact, URL-safe means of representing claims between parties
- **Check Digit**: A digit added to a number for error detection purposes

### 10.3 Reference Documents

1. Google Wallet API Documentation: https://developers.google.com/wallet
2. Luhn Algorithm Specification: ISO/IEC 7812
3. QR Code Standards: ISO/IEC 18004:2015
4. Django Documentation: https://docs.djangoproject.com/
