# Supporter Invoice System - Technical Implementation Guide

## Overview

This guide provides technical implementation details for developers working with the Supporter Invoice System. It covers integration points, code structure, and extension patterns.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Registration  │    │   Geolocation   │    │     Invoice     │
│      Form       │────│   Detection     │────│   Generation    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ SupporterProfile│    │  Location Data  │    │    Invoice      │
│     Model       │    │     Storage     │    │    Storage      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Key Components

### 1. Models

#### SupporterProfile Model
```python
# supporters/models.py
class SupporterProfile(models.Model):
    # Core fields
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    favorite_club = models.ForeignKey(Club, on_delete=models.SET_NULL, null=True, blank=True)
    membership_type = models.CharField(max_length=20, choices=MEMBERSHIP_CHOICES, default='PREMIUM')
    
    # Geolocation fields
    latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    location_city = models.CharField(max_length=100, blank=True)
    location_province = models.CharField(max_length=100, blank=True)
    location_country = models.CharField(max_length=100, blank=True)
    location_accuracy = models.FloatField(blank=True, null=True)
    location_timestamp = models.DateTimeField(blank=True, null=True)
    
    # Invoice integration
    invoice = models.OneToOneField('membership.Invoice', on_delete=models.SET_NULL, null=True, blank=True)
```

### 2. Views

#### Registration View with Invoice Generation
```python
# supporters/views.py
@login_required
def register_supporter(request):
    if request.method == 'POST':
        form = SupporterRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            supporter = form.save(commit=False)
            supporter.user = request.user
            
            # Handle geolocation
            if supporter.latitude and supporter.longitude:
                supporter.location_timestamp = timezone.now()
            
            supporter.save()
            
            # Generate invoice
            invoice = create_supporter_invoice(supporter)
            if invoice:
                supporter.invoice = invoice
                supporter.save()
                
            return redirect('supporters:profile')
```

#### Invoice Creation Function
```python
# supporters/views.py
def create_supporter_invoice(supporter_profile):
    """Create an invoice for a supporter registration"""
    # Get pricing
    amount = MEMBERSHIP_PRICING.get(supporter_profile.membership_type, 0)
    
    # Calculate VAT
    tax_amount = amount * 0.15
    total_amount = amount + tax_amount
    
    # Generate invoice number
    invoice_number = f"SUP-{timezone.now().strftime('%Y%m%d')}-{supporter_profile.id:06d}"
    
    # Create invoice
    invoice = Invoice.objects.create(
        invoice_number=invoice_number,
        invoice_type='REGISTRATION',
        amount=total_amount,
        tax_amount=tax_amount,
        status='PENDING',
        issue_date=timezone.now().date(),
        due_date=timezone.now().date() + timedelta(days=30),
        club=supporter_profile.favorite_club or Club.objects.first(),
        issued_by=get_system_member(),
        notes=f"Supporter registration - {supporter_profile.get_membership_type_display()}"
    )
    
    return invoice
```

### 3. Forms

#### Enhanced Registration Form
```python
# supporters/forms.py
class SupporterRegistrationForm(forms.ModelForm):
    class Meta:
        model = SupporterProfile
        fields = [
            'favorite_club', 'membership_type', 'id_number', 'id_document',
            'date_of_birth', 'address', 'latitude', 'longitude', 
            'location_city', 'location_province', 'location_country',
            'location_accuracy'
        ]
        widgets = {
            # Visible fields
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            
            # Hidden geolocation fields
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'location_city': forms.HiddenInput(),
            'location_province': forms.HiddenInput(),
            'location_country': forms.HiddenInput(),
            'location_accuracy': forms.HiddenInput(),
        }
```

### 4. Admin Integration

#### Enhanced Admin Interface
```python
# supporters/admin.py
@admin.register(SupporterProfile)
class SupporterProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'favorite_club', 'membership_type', 'is_verified', 
        'created_at', 'location_city', 'location_province', 
        'has_location', 'has_invoice'
    )
    
    list_filter = (
        'membership_type', 'is_verified', 'favorite_club', 
        'location_province', 'location_country'
    )
    
    search_fields = (
        'user__first_name', 'user__last_name', 'user__email', 
        'id_number', 'location_city'
    )
    
    fieldsets = (
        (None, {
            'fields': ('user', 'favorite_club', 'membership_type', 'is_verified', 'notes')
        }),
        ('Location Information', {
            'fields': (
                ('latitude', 'longitude'), 
                ('location_city', 'location_province', 'location_country'),
                'location_accuracy', 'location_timestamp'
            )
        }),
        ('Card/Invoice', {
            'fields': ('digital_card', 'physical_card', 'invoice')
        }),
    )
    
    def has_location(self, obj):
        return bool(obj.latitude and obj.longitude)
    has_location.boolean = True
    
    def has_invoice(self, obj):
        return bool(obj.invoice)
    has_invoice.boolean = True
```

## Frontend Implementation

### 1. Geolocation Detection

#### JavaScript Implementation
```javascript
// Geolocation detection
function detectLocation() {
    if (!navigator.geolocation) {
        showError('Geolocation not supported');
        return;
    }
    
    navigator.geolocation.getCurrentPosition(
        function(position) {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            const accuracy = position.coords.accuracy;
            
            // Store coordinates
            document.querySelector('input[name="latitude"]').value = lat;
            document.querySelector('input[name="longitude"]').value = lng;
            document.querySelector('input[name="location_accuracy"]').value = accuracy;
            
            // Reverse geocode
            reverseGeocode(lat, lng);
        },
        function(error) {
            handleGeolocationError(error);
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000
        }
    );
}

// Reverse geocoding
async function reverseGeocode(lat, lng) {
    try {
        const response = await fetch(
            `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lng}&localityLanguage=en`
        );
        const data = await response.json();
        
        // Extract location info
        const city = data.city || data.locality || '';
        const province = data.principalSubdivision || '';
        const country = data.countryName || '';
        
        // Store in hidden fields
        document.querySelector('input[name="location_city"]').value = city;
        document.querySelector('input[name="location_province"]').value = province;
        document.querySelector('input[name="location_country"]').value = country;
        
        // Update address field if empty
        const addressField = document.querySelector('textarea[name="address"]');
        if (!addressField.value.trim()) {
            let address = '';
            if (city) address += city;
            if (province) address += (address ? ', ' : '') + province;
            if (country) address += (address ? ', ' : '') + country;
            addressField.value = address;
        }
        
        showSuccess(`Location detected: ${city}, ${province}`);
        
    } catch (error) {
        console.error('Geocoding error:', error);
        showSuccess('Location coordinates captured successfully');
    }
}
```

### 2. Dynamic Pricing Display

```javascript
// Membership type pricing updates
const membershipSelect = document.querySelector('select[name="membership_type"]');
const familyHighlight = document.querySelector('.family-highlight');

membershipSelect.addEventListener('change', function() {
    const selectedValue = this.value;
    const familyText = familyHighlight.querySelector('strong');
    
    const pricing = {
        'PREMIUM': 'Premium Membership (R172.50): Individual supporter benefits!',
        'VIP': 'VIP Membership (R345.00): Premium individual benefits plus VIP access!',
        'FAMILY_BASIC': 'Family Basic (R517.50): Premium benefits for up to 4 family members!',
        'FAMILY_PREMIUM': 'Family Premium (R1,035.00): VIP benefits for up to 4 family members!',
        'FAMILY_VIP': 'Family VIP (R1,725.00): Ultimate package with exclusive family events!'
    };
    
    familyText.innerHTML = pricing[selectedValue] || 'Select a membership type';
});
```

## Database Schema

### Migration Files

```python
# Migration for geolocation fields
class Migration(migrations.Migration):
    dependencies = [
        ('supporters', '0002_alter_supporterprofile_membership_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='supporterprofile',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=8, help_text='Latitude coordinate', max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='supporterprofile',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=8, help_text='Longitude coordinate', max_digits=11, null=True),
        ),
        # ... other fields
    ]
```

## API Integration

### External Services

#### Geolocation Service
```python
# BigDataCloud API integration
GEOCODING_API_URL = "https://api.bigdatacloud.net/data/reverse-geocode-client"

def reverse_geocode(latitude, longitude):
    """Convert coordinates to address information"""
    try:
        response = requests.get(
            GEOCODING_API_URL,
            params={
                'latitude': latitude,
                'longitude': longitude,
                'localityLanguage': 'en'
            },
            timeout=10
        )
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Geocoding API error: {e}")
        return None
```

### Internal APIs

#### Supporter Profile ViewSet
```python
# supporters/views.py
class SupporterProfileViewSet(viewsets.ModelViewSet):
    queryset = SupporterProfile.objects.all()
    serializer_class = SupporterProfileSerializer
    permission_classes = [IsSupporterSelfOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and hasattr(user, 'supporterprofile'):
            return SupporterProfile.objects.filter(user=user)
        return super().get_queryset()
```

## Configuration

### Settings Configuration

```python
# settings.py

# Supporter system settings
SUPPORTER_SETTINGS = {
    'DEFAULT_PAYMENT_TERMS_DAYS': 30,
    'VAT_RATE': 0.15,
    'MEMBERSHIP_PRICING': {
        'PREMIUM': 150.00,
        'VIP': 300.00,
        'FAMILY_BASIC': 450.00,
        'FAMILY_PREMIUM': 900.00,
        'FAMILY_VIP': 1500.00,
    },
    'GEOLOCATION_TIMEOUT': 10000,
    'GEOLOCATION_MAX_AGE': 300000,
}

# Invoice settings
INVOICE_SETTINGS = {
    'SUPPORTER_PREFIX': 'SUP',
    'AUTOMATIC_GENERATION': True,
    'SYSTEM_ISSUER_EMAIL': 'system@safa.net',
}
```

### URL Configuration

```python
# supporters/urls.py
from django.urls import path, include
from rest_framework import routers
from . import views
from .views import SupporterProfileViewSet

app_name = 'supporters'

router = routers.DefaultRouter()
router.register(r'supporterprofiles', SupporterProfileViewSet)

urlpatterns = [
    path('register/', views.register_supporter, name='register'),
    path('profile/', views.supporter_profile, name='profile'),
    path('api/', include(router.urls)),
]
```

## Testing

### Unit Tests

```python
# supporters/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import SupporterProfile
from .views import create_supporter_invoice

class SupporterInvoiceTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    def test_invoice_generation(self):
        """Test that invoices are generated correctly"""
        profile = SupporterProfile.objects.create(
            user=self.user,
            membership_type='PREMIUM'
        )
        
        invoice = create_supporter_invoice(profile)
        
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice.amount, 172.50)  # 150 + 15% VAT
        self.assertEqual(invoice.tax_amount, 22.50)
        self.assertEqual(invoice.invoice_type, 'REGISTRATION')
        
    def test_family_package_pricing(self):
        """Test family package pricing calculation"""
        profile = SupporterProfile.objects.create(
            user=self.user,
            membership_type='FAMILY_VIP'
        )
        
        invoice = create_supporter_invoice(profile)
        
        self.assertEqual(invoice.amount, 1725.00)  # 1500 + 15% VAT
        self.assertEqual(invoice.tax_amount, 225.00)
```

### Integration Tests

```python
class SupporterRegistrationIntegrationTest(TestCase):
    def test_full_registration_flow(self):
        """Test complete registration with invoice generation"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post('/supporters/register/', {
            'membership_type': 'PREMIUM',
            'address': 'Test Address',
            'latitude': '-26.2041',
            'longitude': '28.0473',
            'location_city': 'Johannesburg',
            'location_province': 'Gauteng',
            'location_country': 'South Africa',
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Check profile created
        profile = SupporterProfile.objects.get(user__username='testuser')
        self.assertEqual(profile.membership_type, 'PREMIUM')
        self.assertEqual(profile.location_city, 'Johannesburg')
        
        # Check invoice created
        self.assertIsNotNone(profile.invoice)
        self.assertEqual(profile.invoice.amount, 172.50)
```

## Security Considerations

### Data Protection
```python
# Encrypt sensitive data
from django.db import models
from encrypted_model_fields.fields import EncryptedCharField

class SupporterProfile(models.Model):
    # Encrypt ID number
    id_number = EncryptedCharField(max_length=64, blank=True)
    
    # Location data privacy
    def anonymize_location(self):
        """Remove precise location data for privacy"""
        self.latitude = None
        self.longitude = None
        self.location_timestamp = None
        self.save()
```

### Input Validation
```python
# Form validation
def clean_id_number(self):
    id_number = self.cleaned_data.get('id_number')
    if id_number and not re.match(r'^\d{13}$', id_number):
        raise ValidationError('ID number must be 13 digits')
    return id_number
```

## Performance Optimization

### Database Indexing
```python
# Add indexes for common queries
class Meta:
    indexes = [
        models.Index(fields=['membership_type']),
        models.Index(fields=['location_province', 'location_city']),
        models.Index(fields=['created_at']),
        models.Index(fields=['user']),
    ]
```

### Query Optimization
```python
# Optimize admin queries
def get_queryset(self):
    return super().get_queryset().select_related(
        'user', 'favorite_club', 'invoice'
    ).prefetch_related('digital_card', 'physical_card')
```

## Deployment Considerations

### Environment Variables
```bash
# .env file
SAFA_VAT_RATE=0.15
SAFA_PAYMENT_TERMS_DAYS=30
GEOCODING_API_KEY=your_api_key_here
SYSTEM_ISSUER_EMAIL=system@safa.net
```

### Static Files
```python
# Ensure geolocation JS is properly served
STATICFILES_DIRS = [
    BASE_DIR / "static",
    BASE_DIR / "supporters" / "static",
]
```

## Monitoring & Logging

### Custom Logging
```python
import logging

logger = logging.getLogger('supporters.invoice')

def create_supporter_invoice(supporter_profile):
    try:
        # Invoice creation logic
        logger.info(f"Invoice created for supporter {supporter_profile.id}")
        return invoice
    except Exception as e:
        logger.error(f"Invoice creation failed for supporter {supporter_profile.id}: {e}")
        return None
```

### Metrics Collection
```python
# Track registration metrics
from django.db.models.signals import post_save

@receiver(post_save, sender=SupporterProfile)
def track_supporter_registration(sender, instance, created, **kwargs):
    if created:
        # Send metrics to monitoring system
        metrics.increment('supporter.registration.success')
        metrics.histogram('supporter.registration.membership_type', 
                         tags={'type': instance.membership_type})
```

---

**Document Version**: 1.0  
**Last Updated**: June 22, 2025  
**Target Audience**: Developers, System Architects  
**Prerequisites**: Django knowledge, SAFA system familiarity
