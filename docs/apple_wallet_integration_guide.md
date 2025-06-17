# Apple Wallet Integration Guide for SAFA Digital Cards

## Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Apple Developer Account Setup](#apple-developer-account-setup)
4. [Pass Type Certificate Creation](#pass-type-certificate-creation)
5. [Pass Design and Structure](#pass-design-and-structure)
6. [Django Integration](#django-integration)
7. [Testing and Deployment](#testing-and-deployment)
8. [User Experience Considerations](#user-experience-considerations)
9. [Maintenance and Updates](#maintenance-and-updates)
10. [Troubleshooting](#troubleshooting)

---

## Introduction

Apple Wallet (formerly Passbook) allows iOS users to store and access membership cards, boarding passes, tickets, and more directly from their Apple devices. This guide outlines the process for integrating SAFA digital cards with Apple Wallet to provide a seamless experience for iOS users, complementing our existing Google Wallet integration.

### Key Benefits

- **Increased Accessibility**: Reach members using iOS devices
- **Lock Screen Integration**: Cards can appear on lock screen based on time/location
- **Automatic Updates**: Push updates to cards when information changes
- **Offline Access**: Members can access their cards without an internet connection
- **Brand Presence**: Increased visibility on members' devices

---

## Prerequisites

Before starting the Apple Wallet integration, ensure you have:

1. **Apple Developer Account**: An active Apple Developer Program membership ($99/year)
2. **macOS Computer**: Required for certificate generation and pass creation
3. **SSL Certificate**: Valid SSL for your production server
4. **Python Libraries**:
   - `passkit` library for Python (for creating and signing passes)
   - `wallet` package for Django integration

---

## Apple Developer Account Setup

### 1. Register as an Apple Developer

1. Go to the [Apple Developer Program](https://developer.apple.com/programs/) website
2. Sign in with your Apple ID
3. Complete the enrollment process
4. Pay the annual fee ($99/year)

### 2. Create an App Identifier

1. Navigate to Certificates, Identifiers & Profiles
2. Select "Identifiers" and click "+"
3. Choose "App IDs" and click "Continue"
4. Select "App" as the type
5. Enter a description (e.g., "SAFA Membership Cards")
6. Enter your Bundle ID (e.g., "za.org.safa.membershipcards")
7. Under Capabilities, enable "Wallet"
8. Click "Continue" and then "Register"

---

## Pass Type Certificate Creation

### 1. Create a Pass Type ID

1. In the Apple Developer portal, go to "Identifiers"
2. Click "+" and select "Pass Type IDs"
3. Enter a description (e.g., "SAFA Membership Pass")
4. Enter a Pass Type ID (e.g., "pass.za.org.safa.membership")
5. Click "Continue" and then "Register"

### 2. Generate Pass Type Certificate

1. Select your newly created Pass Type ID
2. Click "Create Certificate"
3. Follow the instructions to create a Certificate Signing Request (CSR) using Keychain Access
4. Upload the CSR file
5. Download the generated certificate

### 3. Create Pass Package

1. Download the certificate and install it in your Keychain
2. Export the certificate and private key as a .p12 file
3. Set a strong password for the .p12 file
4. Store securely for use in your Django application

---

## Pass Design and Structure

Apple Wallet passes follow a specific JSON structure with visual elements defined in the pass.json file.

### 1. Pass Structure

```
PassStructure/
├── pass.json        # Main configuration file
├── logo.png         # Card logo
├── icon.png         # App icon
├── strip.png        # Optional header image
├── thumbnail.png    # Optional thumbnail
└── manifest.json    # Auto-generated file listing included assets
```

### 2. Sample pass.json

```json
{
  "formatVersion": 1,
  "passTypeIdentifier": "pass.za.org.safa.membership",
  "serialNumber": "SAFA12345678",
  "teamIdentifier": "YOUR_TEAM_ID",
  "webServiceURL": "https://safa.org.za/api/wallet/",
  "authenticationToken": "UNIQUE_TOKEN_PER_PASS",
  "organizationName": "South African Football Association",
  "description": "SAFA Membership Card",
  "logoText": "SAFA",
  "foregroundColor": "rgb(255, 255, 255)",
  "backgroundColor": "rgb(0, 102, 51)",
  "labelColor": "rgb(255, 215, 0)",
  "genericPass": {
    "headerFields": [
      {
        "key": "member_status",
        "label": "STATUS",
        "value": "ACTIVE",
        "textAlignment": "PKTextAlignmentRight"
      }
    ],
    "primaryFields": [
      {
        "key": "member_name",
        "label": "NAME",
        "value": "John Doe"
      }
    ],
    "secondaryFields": [
      {
        "key": "safa_id",
        "label": "SAFA ID",
        "value": "SA123456789"
      },
      {
        "key": "card_number",
        "label": "CARD #",
        "value": "2202512345678"
      }
    ],
    "auxiliaryFields": [
      {
        "key": "membership_type",
        "label": "MEMBERSHIP TYPE",
        "value": "PLAYER"
      },
      {
        "key": "region",
        "label": "REGION",
        "value": "Gauteng"
      }
    ],
    "backFields": [
      {
        "key": "expires",
        "label": "VALID UNTIL",
        "value": "30 JUN 2026",
        "dateStyle": "PKDateStyleMedium"
      },
      {
        "key": "club",
        "label": "CLUB AFFILIATION",
        "value": "Johannesburg FC"
      },
      {
        "key": "qr_code",
        "label": "VERIFICATION QR CODE",
        "value": "SAFA_QR_CODE_DATA"
      },
      {
        "key": "terms",
        "label": "TERMS & CONDITIONS",
        "value": "This card remains the property of SAFA. By using this card, you agree to abide by all SAFA regulations and policies."
      }
    ]
  },
  "barcode": {
    "message": "SAFA_QR_CODE_DATA",
    "format": "PKBarcodeFormatQR",
    "messageEncoding": "utf-8",
    "altText": "SA123456789"
  }
}
```

### 3. Visual Design Requirements

Each image must be provided in multiple resolutions:

- 1x for standard resolution
- 2x for retina displays
- 3x for Super Retina displays

For example:
- icon.png, icon@2x.png, icon@3x.png
- logo.png, logo@2x.png, logo@3x.png

---

## Django Integration

### 1. Install Required Packages

```bash
pip install django-wallet passkit
```

### 2. Update settings.py

```python
# settings.py

# Apple Wallet Settings
APPLE_WALLET_ENABLED = True
APPLE_WALLET_CERTIFICATE_PATH = os.path.join(BASE_DIR, 'credentials', 'safa_wallet_certificate.p12')
APPLE_WALLET_CERTIFICATE_PASSWORD = os.environ.get('APPLE_WALLET_PASSWORD', '')
APPLE_WALLET_PASS_TYPE_ID = 'pass.za.org.safa.membership'
APPLE_WALLET_TEAM_ID = 'YOUR_APPLE_TEAM_ID'
```

### 3. Create Apple Wallet Manager

Create a new file `apple_wallet.py` in the `membership_cards` app:

```python
import os
import tempfile
import json
from django.conf import settings
from passkit.models import Pass, Barcode, BarcodeFormat, StoreCard
from passkit.models import Location, IBeacon

class AppleWalletManager:
    """
    Manages Apple Wallet pass creation and updates
    """
    
    def __init__(self):
        self.certificate_path = settings.APPLE_WALLET_CERTIFICATE_PATH
        self.certificate_password = settings.APPLE_WALLET_CERTIFICATE_PASSWORD
        self.pass_type_id = settings.APPLE_WALLET_PASS_TYPE_ID
        self.team_id = settings.APPLE_WALLET_TEAM_ID
        
        # Base URL for web service
        self.web_service_url = f"{settings.BASE_URL}/api/wallet/"
    
    def is_configured(self):
        """Check if Apple Wallet integration is properly configured"""
        return (
            settings.APPLE_WALLET_ENABLED and
            os.path.exists(self.certificate_path) and
            self.certificate_password and
            self.pass_type_id and
            self.team_id
        )
    
    def create_pass(self, digital_card):
        """Create an Apple Wallet pass for a digital card"""
        if not self.is_configured():
            raise ValueError("Apple Wallet is not configured properly")
        
        # Get user from digital card
        user = digital_card.user
        
        # Create pass instance
        card_pass = Pass(
            pass_type_identifier=self.pass_type_id,
            organization_name='South African Football Association',
            team_identifier=self.team_id
        )
        
        # Set pass metadata
        card_pass.description = f"SAFA Membership Card - {user.get_full_name()}"
        card_pass.serial_number = f"SAFA_{user.safa_id}"
        
        # Set authentication token for push updates
        import uuid
        card_pass.authentication_token = str(uuid.uuid4()).replace('-', '')
        
        # Set web service URL for updates
        card_pass.web_service_url = self.web_service_url
        
        # Set appearance and branding
        card_pass.logo_text = 'SAFA'
        card_pass.foreground_color = 'rgb(255, 255, 255)'
        card_pass.background_color = 'rgb(0, 102, 51)'  # SAFA Green
        card_pass.label_color = 'rgb(255, 215, 0)'  # Gold
        
        # Add barcode (QR code)
        card_pass.barcode = Barcode(
            message=digital_card.qr_code_data,
            format=BarcodeFormat.QR,
            alt_text=user.safa_id
        )
        
        # Create store card style pass
        store_card = StoreCard()
        
        # Add fields for the front of the card
        store_card.add_primary_field('name', user.get_full_name(), 'MEMBER')
        store_card.add_secondary_field('safa_id', user.safa_id, 'SAFA ID')
        store_card.add_secondary_field('card_number', digital_card.card_number, 'CARD #')
        store_card.add_auxiliary_field('expires', digital_card.expires_date.strftime('%d %b %Y'), 'VALID UNTIL')
        store_card.add_auxiliary_field('status', digital_card.status, 'STATUS')
        
        # Add fields for the back of the card
        store_card.add_back_field('club', getattr(user, 'club', 'Not Affiliated'), 'CLUB')
        store_card.add_back_field('terms', 'This card remains the property of SAFA. By using this card, you agree to abide by all SAFA regulations and policies.', 'TERMS & CONDITIONS')
        
        # Add pass structure to the pass
        card_pass.store_card = store_card
        
        # Create temporary directory for pass files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Add pass template files from templates directory
            template_path = os.path.join(settings.BASE_DIR, 'membership_cards', 'apple_wallet_template')
            
            # Generate and save the .pkpass file
            pkpass = card_pass.create(
                self.certificate_path,
                self.certificate_password,
                temp_dir
            )
            
            # Return the pkpass data
            return pkpass
```

### 4. Create a View for Pass Distribution

Update your `views.py` file to include a new view for Apple Wallet:

```python
from .apple_wallet import AppleWalletManager
from django.http import HttpResponse

@login_required
def add_to_apple_wallet(request):
    """Add user's digital card to Apple Wallet"""
    try:
        # Get the user's digital card
        digital_card = request.user.digital_card
        
        # Initialize the Apple Wallet manager
        wallet_manager = AppleWalletManager()
        
        if not wallet_manager.is_configured():
            # If Apple Wallet is not configured, show a message
            return render(request, 'membership_cards/wallet_not_configured.html', {
                'wallet_type': 'Apple Wallet'
            })
        
        # Generate the .pkpass file
        pkpass = wallet_manager.create_pass(digital_card)
        
        # Return the pass as a download
        response = HttpResponse(pkpass, content_type='application/vnd.apple.pkpass')
        response['Content-Disposition'] = f'attachment; filename=SAFA_Membership_{digital_card.card_number}.pkpass'
        return response
    
    except DigitalCard.DoesNotExist:
        # User doesn't have a digital card
        return render(request, 'membership_cards/no_card.html')
    
    except Exception as e:
        # Generic error handling
        return render(request, 'membership_cards/wallet_error.html', {
            'error': str(e),
            'wallet_type': 'Apple Wallet'
        })
```

### 5. Add URL Route

Update your `urls.py`:

```python
path('apple-wallet/', views.add_to_apple_wallet, name='apple_wallet'),
```

### 6. Create Template Assets

Create a directory for Apple Wallet template assets:

```bash
mkdir -p membership_cards/apple_wallet_template
```

Add the required image files in all resolutions (1x, 2x, 3x):
- logo.png
- icon.png
- strip.png (optional)

---

## Testing and Deployment

### 1. Testing on Development Devices

1. Create a Pass Type ID for development
2. Generate test passes using the Python script
3. Email the .pkpass file to your test device
4. Tap the attachment to add it to Apple Wallet

### 2. Web Service Implementation

1. Implement registration endpoint for device registrations
2. Create push notification endpoint for pass updates
3. Set up pass update logic when member information changes

### 3. Production Deployment Checklist

- [ ] Production Pass Type ID configured
- [ ] Production certificates installed
- [ ] SSL enabled for web service
- [ ] Push notification service tested
- [ ] Pass visual design verified on multiple iOS devices

---

## User Experience Considerations

### 1. Cross-Platform Strategy

Provide a unified experience across both Google Wallet and Apple Wallet:
- Consistent visual design
- Same information displayed on both platforms
- Equal feature support when possible

### 2. Device Detection

Implement device detection on the frontend:
- Show "Add to Apple Wallet" button for iOS users
- Show "Add to Google Wallet" button for Android users
- Show both options for desktop users

Example implementation:

```javascript
document.addEventListener('DOMContentLoaded', () => {
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
  const isAndroid = /Android/.test(navigator.userAgent);
  
  const appleWalletBtn = document.getElementById('apple-wallet-btn');
  const googleWalletBtn = document.getElementById('google-wallet-btn');
  
  if (isIOS) {
    appleWalletBtn.style.display = 'block';
    googleWalletBtn.style.display = 'none';
  } else if (isAndroid) {
    appleWalletBtn.style.display = 'none';
    googleWalletBtn.style.display = 'block';
  } else {
    appleWalletBtn.style.display = 'block';
    googleWalletBtn.style.display = 'block';
  }
});
```

---

## Maintenance and Updates

### 1. Certificate Renewal

Apple certificates expire annually. Set up a reminder to:
1. Renew Pass Type Certificate in Apple Developer Portal
2. Update the certificate file in your system
3. Test that passes are still working correctly

### 2. Push Updates to Existing Passes

When member information changes:
1. Query the registrations database to find registered devices
2. Send push notifications to those devices
3. Provide updated pass data when devices request it

Example update code:
```python
def update_member_passes(member):
    """Send updates to all devices with this member's pass"""
    from .models import PassRegistration
    
    # Find all registered devices for this member
    registrations = PassRegistration.objects.filter(
        serial_number=f"SAFA_{member.safa_id}"
    )
    
    # For each registration, send a push notification
    for reg in registrations:
        try:
            send_push_notification(reg.push_token, reg.device_library_id)
        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Pass Won't Install on Device

**Issue**: The .pkpass file downloads but won't install on iOS devices.
**Solution**:
- Verify the certificate is properly signed and not expired
- Ensure the pass.json structure is valid
- Check that all required images are included
- Validate that the MIME type is 'application/vnd.apple.pkpass'

#### 2. Push Updates Not Working

**Issue**: Changes to member information aren't reflected in the Apple Wallet pass.
**Solution**:
- Verify web service URL is accessible from the internet
- Check SSL certificate is valid
- Ensure authentication token is properly set
- Validate push notification requests format

#### 3. Missing Images in Pass

**Issue**: Some images don't appear in the pass on certain devices.
**Solution**:
- Verify all required resolutions are included (1x, 2x, 3x)
- Check image dimensions match Apple requirements
- Ensure file names are correct (case-sensitive)
- Validate image formats (PNG recommended)

---

## Resources

1. [Apple Wallet Developer Documentation](https://developer.apple.com/documentation/walletpasses)
2. [Passkit Python Library](https://github.com/devartis/passbook)
3. [Django-Wallet Package](https://pypi.org/project/django-wallet/)
4. [Pass Design Guidelines](https://developer.apple.com/design/human-interface-guidelines/wallet)

---

*Last Updated: June 17, 2025*
