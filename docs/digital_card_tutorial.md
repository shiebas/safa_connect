# SAFA Digital Card Implementation Tutorial

This tutorial provides step-by-step instructions for implementing the SAFA digital card system with Google Wallet integration and Luhn algorithm validation.

## Prerequisites

Before beginning this implementation, ensure you have:

1. A Django project set up with user authentication
2. Basic understanding of Django models, views, and templates
3. Access to Google Cloud Platform (for Google Wallet integration)
4. Python 3.8+ installed

## Step 1: Set Up the Base Digital Card Model

First, create a model to represent the digital membership card:

```python
# membership_cards/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
import os

class DigitalCard(models.Model):
    """Digital membership card model"""
    
    CARD_STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('EXPIRED', 'Expired'),
        ('REVOKED', 'Revoked')
    ]
    
    # Link to user
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='digital_card'
    )
    
    # Card identification
    card_number = models.CharField(
        max_length=16,  # Updated to 16 digits for banking standard
        unique=True,
        help_text='Unique card number (auto-generated)'
    )
    card_uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text='Unique identifier for QR code security'
    )
    
    # Card status and dates
    status = models.CharField(
        max_length=20,
        choices=CARD_STATUS_CHOICES,
        default='ACTIVE'
    )
    issued_date = models.DateTimeField(auto_now_add=True)
    expires_date = models.DateField(
        help_text='Card expiry date (syncs with membership expiry)'
    )
    last_updated = models.DateTimeField(auto_now=True)
    
    # QR Code data
    qr_code_data = models.TextField(
        blank=True,
        help_text='Encrypted data for QR code'
    )
    qr_code_version = models.IntegerField(
        default=1,
        help_text='QR code version for security updates'
    )
    
    # Add QR image field
    qr_image = models.ImageField(
        upload_to='qr_codes/',
        blank=True,
        null=True,
        help_text='Generated QR code image with logo'
    )
    
    class Meta:
        verbose_name = 'Digital Card'
        verbose_name_plural = 'Digital Cards'
        ordering = ['-issued_date']
    
    def __str__(self):
        return f"Digital Card #{self.card_number} - {self.user.get_full_name()}"
```

## Step 2: Implement Luhn Algorithm for Card Validation

Add methods to generate and validate card numbers using the Luhn algorithm:

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
    
def verify_luhn_algorithm(self, card_number):
    """Verify if a card number passes the Luhn algorithm check"""
    # Remove any spaces or dashes
    card_number = card_number.replace(" ", "").replace("-", "")
    
    if not card_number.isdigit():
        return False
        
    # Get all digits except the last one
    main_digits = card_number[:-1]
    check_digit = card_number[-1]
    
    # Calculate what the check digit should be
    calculated_check = self.generate_luhn_check_digit(main_digits)
    
    # Compare with the actual check digit
    return calculated_check == check_digit

def generate_card_number(self):
    """Generate unique 16-digit card number using Luhn algorithm"""
    while True:
        # Format: 2 (SAFA prefix) + YYYY (year) + 9 random digits
        year = timezone.now().year
        prefix = "2"  # SAFA prefix
        random_part = get_random_string(9, allowed_chars='0123456789')
        
        # Combine to get 15 digits (without check digit)
        partial_number = f"{prefix}{year}{random_part}"
        
        # Generate the check digit using Luhn algorithm
        check_digit = self.generate_luhn_check_digit(partial_number)
        
        # Create the 16-digit card number
        card_number = f"{partial_number}{check_digit}"
        
        if not DigitalCard.objects.filter(card_number=card_number).exists():
            self.card_number = card_number
            break
```

## Step 3: Create QR Code Generation Functions

Add methods to generate secure QR codes:

```python
def generate_qr_data(self):
    """Generate optimized QR code data with size limits"""
    from django.core import signing
    
    # Debug: Check if we have required data
    if not self.user.safa_id:
        # Generate SAFA ID if missing
        self.user.generate_safa_id()
        self.user.save()
    
    # Compact data structure (under 1000 characters)
    qr_data = {
        'id': str(self.card_uuid)[:8],  # Shortened UUID
        'u': self.user.id,
        'n': f"{self.user.name} {self.user.surname}"[:30],  # Limit name length
        's': self.user.safa_id,
        'c': self.card_number,
        'st': self.status[0],  # Single character status
        'exp': self.expires_date.strftime('%Y%m%d'),  # Compact date
        'v': self.qr_code_version,
        't': 'D'  # Digital card type
    }
    
    # Sign and encode (this creates our security)
    signed_data = signing.dumps(qr_data)
    self.qr_code_data = signed_data

def generate_qr_image(self):
    """Generate QR code image with SAFA logo"""
    try:
        import qrcode
        from qrcode.image.pure import PymagingImage
        from PIL import Image
        import io
        from django.core.files.base import ContentFile
        
        # Ensure we have QR data first
        if not self.qr_code_data:
            self.generate_qr_data()
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(self.qr_code_data)
        qr.make(fit=True)
        
        # Create QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to model field
        buffer = io.BytesIO()
        qr_img.save(buffer, format='PNG')
        filename = f"qr_{self.card_number}_{self.qr_code_version}.png"
        
        self.qr_image.save(filename, ContentFile(buffer.getvalue()), save=False)
        return True
        
    except Exception as e:
        print(f"Failed to generate QR image: {str(e)}")
        return False
        
def get_qr_base64(self):
    """Get QR code as base64 for web display"""
    if self.qr_image:
        try:
            with open(self.qr_image.path, 'rb') as img_file:
                import base64
                img_str = base64.b64encode(img_file.read()).decode()
                return f"data:image/png;base64,{img_str}"
        except:
            pass
    return None

def is_valid(self):
    """Check if card is currently valid"""
    if self.status != 'ACTIVE':
        return False
        
    if self.expires_date < timezone.now().date():
        self.status = 'EXPIRED'
        self.save(update_fields=['status'])
        return False
        
    return True
```

## Step 4: Create the Digital Card Template

Create a beautiful, bank-card-like template in your Django templates directory:

```html
{% extends 'base.html' %}
{% load static %}

{% block title %}My SAFA Digital Card{% endblock %}

{% block extra_css %}
<style>
    /* Card flip container */
    .flip-card {
        perspective: 1000px;
        width: 100%;
        max-width: 400px;
        margin: 20px auto;
        height: 250px;
    }
    
    .flip-card-inner {
        position: relative;
        width: 100%;
        height: 100%;
        text-align: center;
        transition: transform 0.6s;
        transform-style: preserve-3d;
    }
    
    .flip-card.flipped .flip-card-inner {
        transform: rotateY(180deg);
    }
    
    .digital-card, .card-back {
        position: absolute;
        width: 100%;
        height: 100%;
        -webkit-backface-visibility: hidden;
        backface-visibility: hidden;
        border-radius: 15px;
        overflow: hidden;
    }
    
    .digital-card {
        background: linear-gradient(135deg, #006633 0%, #004422 100%);
        padding: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        color: #fff;
        position: relative;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .card-back {
        background: linear-gradient(135deg, #004422 0%, #003311 100%);
        transform: rotateY(180deg);
        padding: 20px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    
    .magnetic-strip {
        position: absolute;
        top: 40px;
        left: 0;
        width: 100%;
        height: 40px;
        background-color: #333;
        opacity: 0.8;
    }
    
    /* Card elements styling */
    .card-header {
        text-align: center;
        margin-bottom: 20px;
    }
    
    .safa-logo {
        width: 60px;
        height: 60px;
        margin-bottom: 10px;
    }
    
    .card-title {
        font-size: 16px;
        font-weight: bold;
        color: #FFD700;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .member-photo {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        border: 2px solid #FFD700;
        float: right;
        margin-left: 15px;
        object-fit: cover;
        box-shadow: 0 0 10px rgba(255,215,0,0.3);
    }
    
    .member-info {
        overflow: hidden;
        padding-top: 10px;
        position: relative;
        z-index: 2;
    }
    
    .member-name {
        font-size: 18px;
        font-weight: bold;
        color: #fff;
        margin: 0 0 5px 0;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        letter-spacing: 0.5px;
    }
    
    .member-details {
        font-size: 13px;
        color: rgba(255,255,255,0.85);
        line-height: 1.4;
    }
    
    /* Card number formatting */
    .card-number {
        font-family: 'Courier New', monospace;
        font-size: 16px;
        font-weight: bold;
        color: #FFD700;
        letter-spacing: 3px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.4);
        margin-bottom: 8px;
        display: block;
    }
    
    .chip-icon {
        position: absolute;
        top: 70px;
        left: 20px;
        width: 40px;
        height: 30px;
        background: linear-gradient(145deg, #FFD700, #DAA520);
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        z-index: 3;
    }
    
    /* Additional card elements */
    .validity {
        font-size: 11px;
        color: rgba(255,255,255,0.9);
        margin-top: 4px;
        text-transform: uppercase;
        letter-spacing: 1px;
        display: flex;
        align-items: center;
    }
    
    .safa-id {
        font-size: 11px;
        color: rgba(255,255,255,0.9);
        margin-top: 6px;
        letter-spacing: 0.5px;
        font-family: 'Courier New', monospace;
    }
    
    .status-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 10px;
        font-weight: bold;
        margin-top: 8px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .status-active {
        background: #28a745;
        color: white;
    }
    
    .status-suspended {
        background: #dc3545;
        color: white;
    }
    
    .status-expired {
        background: #6c757d;
        color: white;
    }
    
    .qr-section {
        text-align: center;
        margin-top: 10px;
        padding-top: 15px;
        border-top: 1px solid rgba(255,215,0,0.5);
        position: relative;
        z-index: 2;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .qr-code {
        width: 90px;
        height: 90px;
        background: #fff;
        padding: 6px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }
    
    .qr-code img {
        width: 100%;
        height: 100%;
    }
    
    .card-info {
        flex: 1;
        text-align: right;
        padding-left: 15px;
    }
    
    .card-actions {
        margin-top: 15px;
        text-align: center;
        position: relative;
        z-index: 3;
    }
    
    .btn-card {
        background: rgba(0,0,0,0.3);
        color: #FFD700;
        border: 1px solid #FFD700;
        padding: 8px 16px;
        border-radius: 20px;
        margin: 4px;
        text-decoration: none;
        display: inline-block;
        font-weight: bold;
        transition: all 0.2s ease;
    }
    
    .btn-card:hover {
        background: #FFD700;
        color: #004422;
        text-decoration: none;
    }
</style>
{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="flip-card">
        <div class="flip-card-inner">
            <div class="digital-card">
                <!-- Header -->
                <div class="card-header">
                    <img src="{% static 'images/default_logo.png' %}" alt="SAFA Logo" class="safa-logo">
                    <h2 class="card-title">SOUTH AFRICAN FOOTBALL ASSOCIATION</h2>
                    <p style="margin: 0; font-size: 12px; color: #FFD700; letter-spacing: 1px;">DIGITAL MEMBERSHIP CARD</p>
                </div>
                
                <!-- Member Info -->
                <div class="member-section">
                    {% if user.profile_photo %}
                    <img src="{{ user.profile_photo.url }}" alt="Profile Photo" class="member-photo">
                    {% else %}
                    <div class="member-photo" style="background: #ccc; display: flex; align-items: center; justify-content: center; font-size: 24px; color: #666;">
                        <i class="fas fa-user"></i>
                    </div>
                    {% endif %}
                    
                    <div class="member-info">
                        <h3 class="member-name">{{ user.name }} {{ user.surname }}</h3>
                        <div class="member-details">
                            <strong>SAFA ID:</strong> {{ user.safa_id }}<br>
                            <strong>Role:</strong> {{ user.get_role_display }}<br>
                            <strong>Member Since:</strong> {{ user.date_joined|date:"M Y" }}
                        </div>
                    </div>
                    <div style="clear: both;"></div>
                </div>
                
                <!-- Bank Card Elements -->
                <div class="chip-icon"></div>
                
                <!-- QR Code Section -->
                <div class="qr-section">
                    <div class="qr-code">
                        {% if qr_base64 %}
                        <img src="{{ qr_base64 }}" alt="QR Code">
                        {% else %}
                        <div style="display: flex; align-items: center; justify-content: center; height: 100%; font-size: 12px; color: #666;">
                            QR Code<br>Generating...
                        </div>
                        {% endif %}
                    </div>
                    
                    <div class="card-info">
                        <div class="card-number">{{ card.card_number|slice:":4" }} {{ card.card_number|slice:"4:8" }} {{ card.card_number|slice:"8:12" }} {{ card.card_number|slice:"12:16" }}</div>
                        
                        <div class="validity">
                            {{ card.expires_date|date:"m/y" }}
                        </div>
                        
                        <div class="safa-id">SAFA ID: {{ user.safa_id }}</div>
                        
                        <div class="status-badge status-{{ card.status|lower }}">
                            {{ card.get_status_display }}
                        </div>
                    </div>
                </div>
                
                <!-- Actions -->
                <div class="card-actions">
                    <a href="{% url 'membership_cards:download_card' %}" class="btn-card">
                        <i class="fas fa-download"></i> Download
                    </a>
                    <button onclick="shareCard()" class="btn-card">
                        <i class="fas fa-share"></i> Share
                    </button>
                    <button onclick="flipCard()" class="btn-card">
                        <i class="fas fa-sync-alt"></i> Flip
                    </button>
                    <a href="{% url 'membership_cards:google_wallet' %}" class="btn-card">
                        <i class="fab fa-google"></i> Add to Wallet
                    </a>
                </div>
            </div>
            
            <!-- Card Back Side -->
            <div class="card-back">
                <div class="magnetic-strip"></div>
                
                <div class="qr-code" style="margin: 20px 0;">
                    {% if qr_base64 %}
                    <img src="{{ qr_base64 }}" alt="QR Code">
                    {% else %}
                    <div style="display: flex; align-items: center; justify-content: center; height: 100%; font-size: 12px; color: #666;">
                        QR Code<br>Generating...
                    </div>
                    {% endif %}
                </div>
                
                <div style="color: #FFD700; font-size: 12px; text-align: center; max-width: 80%;">
                    <p>Scan this QR code to verify membership status.</p>
                    <p style="font-size: 10px; color: rgba(255,255,255,0.6); margin-top: 20px;">
                        This card remains the property of SAFA.<br>
                        If found, please return to nearest SAFA office.
                    </p>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Additional Card Actions Outside Card -->
    <div style="text-align: center; margin: 20px auto; max-width: 400px;">
        <button onclick="flipCard()" class="btn btn-dark">
            <i class="fas fa-sync-alt"></i> Flip Card
        </button>
    </div>
</div>

<script>
function shareCard() {
    if (navigator.share) {
        navigator.share({
            title: 'My SAFA Digital Card',
            text: 'Check out my SAFA membership card',
            url: window.location.href
        });
    } else {
        // Fallback for browsers without Web Share API
        if (navigator.clipboard) {
            navigator.clipboard.writeText(window.location.href);
            alert('Card link copied to clipboard!');
        }
    }
}

function flipCard() {
    document.querySelector('.flip-card').classList.toggle('flipped');
}

// Add 3D effects with mouse movement (credit card effect)
document.addEventListener('DOMContentLoaded', function() {
    const card = document.querySelector('.digital-card');
    
    if (window.innerWidth > 768) {  // Only on desktop
        document.addEventListener('mousemove', function(e) {
            const flipCard = document.querySelector('.flip-card');
            if (flipCard.classList.contains('flipped')) return;
            
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateY = (x - centerX) / 15;
            const rotateX = (centerY - y) / 15;
            
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        });
        
        document.addEventListener('mouseleave', function() {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0)';
        });
    }
});
</script>
{% endblock %}
```

## Step 5: Implement Google Wallet Integration

Create a separate file for managing Google Wallet integration:

```python
# membership_cards/google_wallet.py
import json
import time
import uuid
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
import datetime
from django.conf import settings
import os

class GoogleWalletManager:
    """
    Handles creation and management of Google Wallet passes
    """
    
    def __init__(self):
        self.base_url = "https://walletobjects.googleapis.com/walletobjects/v1"
        self.batch_url = "https://walletobjects.googleapis.com/batch"
        self.class_url = f"{self.base_url}/genericClass"
        self.object_url = f"{self.base_url}/genericObject"
        
        # Try to load credentials from settings or environment
        self.credentials = None
        self.service_account_email = getattr(settings, 'GOOGLE_WALLET_SERVICE_ACCOUNT_EMAIL', None)
        
        # Path to service account key
        key_file_path = getattr(settings, 'GOOGLE_WALLET_KEY_FILE', None) 
        
        # This allows for easy development/production switches
        if key_file_path and os.path.exists(key_file_path):
            self.credentials = service_account.Credentials.from_service_account_file(
                key_file_path,
                scopes=['https://www.googleapis.com/auth/wallet_object.issuer']
            )

    def is_configured(self):
        """Check if Google Wallet is properly configured"""
        return self.credentials is not None
        
    def get_authorized_session(self):
        """Get an authorized session for API requests"""
        if not self.is_configured():
            raise ValueError("Google Wallet is not configured. Please set up service account credentials.")
        
        return AuthorizedSession(self.credentials)
        
    def create_class(self, issuer_id, class_suffix):
        """Create a pass class (template) for SAFA membership cards"""
        # Form full class ID
        class_id = f"{issuer_id}.{class_suffix}"
        
        # Define pass class data
        generic_class = {
            'id': class_id,
            'classTemplateInfo': {
                'cardRowTemplateInfos': [
                    {
                        'twoItems': {
                            'startItem': {
                                'firstValue': {
                                    'fields': [
                                        {
                                            'fieldPath': 'object.textModulesData["member_since"]'
                                        }
                                    ]
                                }
                            },
                            'endItem': {
                                'firstValue': {
                                    'fields': [
                                        {
                                            'fieldPath': 'object.textModulesData["expires"]'
                                        }
                                    ]
                                }
                            }
                        }
                    }
                ]
            },
            'imageModulesData': [
                {
                    'mainImage': {
                        'sourceUri': {
                            'uri': f"{settings.BASE_URL}/static/images/safa_logo_small.png"
                        },
                        'contentDescription': {
                            'defaultValue': {
                                'language': 'en-US',
                                'value': 'SAFA Logo'
                            }
                        }
                    }
                }
            ],
            'textModulesData': [
                {
                    'header': {
                        'defaultValue': {
                            'language': 'en-US',
                            'value': 'South African Football Association'
                        }
                    },
                    'body': {
                        'defaultValue': {
                            'language': 'en-US',
                            'value': 'Official Membership Card'
                        }
                    }
                }
            ],
            'linksModuleData': {
                'uris': [
                    {
                        'uri': 'https://www.safa.net/',
                        'description': 'SAFA Website'
                    },
                    {
                        'uri': f"{settings.BASE_URL}/membership-cards/verify/",
                        'description': 'Verify Card'
                    }
                ]
            },
            'hexBackgroundColor': '#006633',
            'heroImage': {
                'sourceUri': {
                    'uri': f"{settings.BASE_URL}/static/images/default_logo.png"
                }
            }
        }
        
        try:
            session = self.get_authorized_session()
            response = session.post(
                self.class_url, 
                json=generic_class
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                # If class already exists, try to get it
                if response.status_code == 409:  # Conflict - resource already exists
                    get_response = session.get(f"{self.class_url}/{class_id}")
                    if get_response.status_code == 200:
                        return get_response.json()
                
                raise Exception(f"Error creating pass class: {response.text}")
                
        except Exception as e:
            raise Exception(f"Error creating pass class: {str(e)}")
    
    def create_wallet_object(self, issuer_id, class_suffix, digital_card):
        """Create a Google Wallet pass object for a specific member"""
        # Get user from digital card
        user = digital_card.user
        
        # Form full class and object IDs
        class_id = f"{issuer_id}.{class_suffix}"
        object_id = f"{class_id}.{user.safa_id}_{int(time.time())}"
        
        # Format dates
        issued_date = digital_card.issued_date.strftime("%Y-%m-%d")
        expires_date = digital_card.expires_date.strftime("%Y-%m-%d")
        
        # Create the pass object
        generic_object = {
            'id': object_id,
            'classId': class_id,
            'genericType': 'GENERIC_TYPE_UNSPECIFIED',
            'hexBackgroundColor': '#006633',
            'logo': {
                'sourceUri': {
                    'uri': f"{settings.BASE_URL}/static/images/safa_logo_small.png"
                },
                'contentDescription': {
                    'defaultValue': {
                        'language': 'en-US',
                        'value': 'SAFA Logo'
                    }
                }
            },
            'cardTitle': {
                'defaultValue': {
                    'language': 'en-US',
                    'value': 'SAFA Membership Card'
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
            'textModulesData': [
                {
                    'id': 'member_since',
                    'header': 'Member Since',
                    'body': issued_date
                },
                {
                    'id': 'expires',
                    'header': 'Expires',
                    'body': expires_date
                },
                {
                    'id': 'card_number',
                    'header': 'Card Number',
                    'body': digital_card.card_number
                },
                {
                    'id': 'membership_type',
                    'header': 'Type',
                    'body': user.get_role_display() if hasattr(user, 'get_role_display') else 'Member'
                }
            ],
            'barcode': {
                'type': 'QR_CODE',
                'value': digital_card.qr_code_data,
                'alternateText': digital_card.card_number
            },
            'heroImage': {
                'sourceUri': {
                    'uri': f"{settings.BASE_URL}/static/images/default_logo.png"
                }
            },
            'state': 'ACTIVE' if digital_card.status == 'ACTIVE' else 'INACTIVE'
        }
        
        try:
            session = self.get_authorized_session()
            response = session.post(
                self.object_url,
                json=generic_object
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                # If object already exists, try to update it
                if response.status_code == 409:  # Conflict
                    # Try to get the existing object
                    get_response = session.get(f"{self.object_url}/{object_id}")
                    if get_response.status_code == 200:
                        # Update the existing object
                        patch_response = session.patch(
                            f"{self.object_url}/{object_id}",
                            json=generic_object
                        )
                        if patch_response.status_code == 200:
                            return patch_response.json()
                
                raise Exception(f"Error creating wallet object: {response.text}")
                
        except Exception as e:
            raise Exception(f"Error creating wallet object: {str(e)}")
    
    def create_jwt_token(self, issuer_id, class_suffix, digital_card):
        """
        Create a signed JWT that can be used to add a pass to Google Wallet
        """
        if not self.is_configured():
            return None
        
        # Get user from digital card
        user = digital_card.user
        
        try:
            # Create class and object first to ensure they exist
            self.create_class(issuer_id, class_suffix)
            wallet_object = self.create_wallet_object(issuer_id, class_suffix, digital_card)
            
            # Form full class and object IDs
            class_id = f"{issuer_id}.{class_suffix}"
            object_id = f"{class_id}.{user.safa_id}_{int(time.time())}"
            
            # Create the JWT payload
            payload = {
                'iss': self.service_account_email,
                'aud': 'google',
                'typ': 'savetowallet',
                'iat': int(time.time()),
                'payload': {
                    'genericObjects': [
                        {
                            'id': object_id,
                            'classId': class_id
                        }
                    ]
                }
            }
            
            # Sign the JWT
            token = self.credentials.sign_jwt(payload, expiry=None)
            
            return token
            
        except Exception as e:
            print(f"Error creating JWT token: {str(e)}")
            return None
```

## Step 6: Create Views for the Digital Card and Google Wallet

Create the views to handle card display and Google Wallet integration:

```python
# membership_cards/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import get_user_model
from django.core import signing
from django.utils import timezone
from django.conf import settings
import base64

from .models import DigitalCard, PhysicalCard
from .google_wallet import GoogleWalletManager

User = get_user_model()

@login_required
def my_digital_card(request):
    """Display user's digital membership card"""
    try:
        digital_card = request.user.digital_card
        context = {
            'card': digital_card,
            'user': request.user,
            'qr_base64': digital_card.get_qr_base64(),
        }
        return render(request, 'membership_cards/digital_card.html', context)
    except DigitalCard.DoesNotExist:
        return render(request, 'membership_cards/no_card.html')

@login_required
def add_to_google_wallet(request):
    """Add user's digital card to Google Wallet"""
    try:
        # Get the user's digital card
        digital_card = request.user.digital_card
        
        # Initialize the Google Wallet manager
        wallet_manager = GoogleWalletManager()
        
        if not wallet_manager.is_configured():
            # If Google Wallet is not configured, show a message
            return render(request, 'membership_cards/wallet_not_configured.html')
        
        # Set issuer ID and class suffix from settings or use defaults
        issuer_id = getattr(settings, 'GOOGLE_WALLET_ISSUER_ID', '3388000000022222228')
        class_suffix = 'SAFAMembershipCard'
        
        # Generate the JWT token for adding to Google Wallet
        jwt_token = wallet_manager.create_jwt_token(issuer_id, class_suffix, digital_card)
        
        if jwt_token:
            # Construct the save URL with the JWT token
            save_url = f"https://pay.google.com/gp/v/save/{jwt_token}"
            
            # Context for the template
            context = {
                'save_url': save_url,
                'card': digital_card,
                'user': request.user
            }
            
            return render(request, 'membership_cards/add_to_google_wallet.html', context)
        else:
            # Failed to create JWT token
            return render(request, 'membership_cards/wallet_error.html', {
                'error': 'Failed to create wallet token'
            })
    
    except DigitalCard.DoesNotExist:
        # User doesn't have a digital card
        return render(request, 'membership_cards/no_card.html')
    
    except Exception as e:
        # Generic error handling
        return render(request, 'membership_cards/wallet_error.html', {
            'error': str(e)
        })
```

## Step 7: Configure URLs for the Digital Card System

Set up URLs for the digital card system:

```python
# membership_cards/urls.py
from django.urls import path, include
from . import views

app_name = 'membership_cards'

urlpatterns = [
    path('my-card/', views.my_digital_card, name='my_card'),
    path('qr-code/', views.card_qr_code, name='qr_code'),
    path('verify/', views.verify_qr_code, name='verify_qr'),
    path('download/', views.download_card, name='download_card'),
    path('google-wallet/', views.add_to_google_wallet, name='google_wallet'),
    path('dashboard/', views.system_dashboard, name='dashboard'),
]
```

## Step 8: Configure Google Wallet Settings

Add Google Wallet settings to your `settings.py` file:

```python
# settings.py

# Google Wallet Settings
GOOGLE_WALLET_ENABLED = True
GOOGLE_WALLET_ISSUER_ID = '3388000000022222228'  # Replace with actual issuer ID in production
GOOGLE_WALLET_SERVICE_ACCOUNT_EMAIL = 'safa-wallet-service@safa-global.iam.gserviceaccount.com'  # Replace with actual service account
GOOGLE_WALLET_KEY_FILE = os.path.join(BASE_DIR, 'credentials', 'google_wallet_key.json')  # Path to service account key file

# Create directory for credentials if it doesn't exist
os.makedirs(os.path.join(BASE_DIR, 'credentials'), exist_ok=True)

# Base URL for generating absolute URLs (for Google Wallet integration)
BASE_URL = 'https://safa.org.za'  # Replace with actual domain in production
if DEBUG:
    BASE_URL = 'http://localhost:8000'
```

## Step 9: Create Google Wallet Template

Create a template for adding cards to Google Wallet:

```html
{% extends 'base.html' %}
{% load static %}

{% block title %}Add to Google Wallet - SAFA Digital Card{% endblock %}

{% block extra_css %}
<style>
    .wallet-container {
        max-width: 500px;
        margin: 40px auto;
        text-align: center;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        background: #ffffff;
    }
    
    .wallet-logo {
        width: 100px;
        margin: 0 auto 20px;
    }
    
    .wallet-button {
        display: inline-block;
        background: #000000;
        color: #ffffff;
        border: none;
        padding: 12px 25px;
        border-radius: 25px;
        text-decoration: none;
        font-size: 16px;
        margin: 20px 0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .wallet-button:hover {
        background: #333333;
        transform: translateY(-2px);
    }
    
    .card-preview {
        max-width: 350px;
        margin: 20px auto;
        border-radius: 15px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        overflow: hidden;
    }
</style>
{% endblock %}

{% block content %}
<div class="container">
    <div class="wallet-container">
        <img src="https://developers.google.com/static/wallet/images/google-wallet.svg" alt="Google Wallet Logo" class="wallet-logo">
        
        <h2>Add Your SAFA Membership Card to Google Wallet</h2>
        <p class="mb-4">Keep your digital membership card on your phone for easy access.</p>
        
        <div class="card-preview">
            <img src="{{ card.get_qr_base64 }}" alt="Card Preview" style="width: 100%;">
        </div>
        
        <a href="{{ save_url }}" class="wallet-button">
            <i class="fab fa-google me-2"></i> Add to Google Wallet
        </a>
        
        <div class="mt-3">
            <a href="{% url 'membership_cards:my_card' %}" class="btn btn-outline-secondary">
                <i class="fas fa-arrow-left me-2"></i> Back to My Card
            </a>
        </div>
    </div>
</div>
{% endblock %}
```

## Step 10: Testing and Deployment

1. **Install Required Packages**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Database Migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Set Up Google Wallet API**:
   - Create a Google Cloud project
   - Enable Google Wallet API
   - Create a service account with Google Wallet API permissions
   - Generate and download the service account key file
   - Place the key file in your credentials directory

4. **Test the Digital Card System**:
   - Log in as a user with a membership
   - Navigate to the "My Card" section
   - Check that the card displays correctly
   - Test the QR code verification
   - Try adding to Google Wallet

5. **Deploy to Production**:
   - Update BASE_URL setting to your production URL
   - Ensure all security settings are configured for production
   - Update GOOGLE_WALLET_ISSUER_ID to your production ID

## Troubleshooting

- **QR Code Not Generating**: Check that PIL and qrcode packages are installed
- **Google Wallet Error**: Verify service account credentials are valid
- **Card Number Issues**: Check that Luhn algorithm implementation is correct
- **Card Not Displaying**: Ensure user has an associated digital card object

## Conclusion

You have now implemented a complete digital card system with Luhn algorithm validation and Google Wallet integration. This modern system provides users with a professional, bank card-like experience for their SAFA membership cards.

For further assistance or to report issues, please contact the SAFA development team.
