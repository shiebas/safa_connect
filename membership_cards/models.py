from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.crypto import get_random_string
import uuid
import os
from .qr_generator import generate_qr_with_logo, qr_to_base64

class DigitalCard(models.Model):
    """Digital membership card model"""
    
    CARD_STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('EXPIRED', 'Expired'),
        ('REVOKED', 'Revoked'),
        ('YELLOW CARD', 'Yellow Card')
    ]
    
    # Link to user
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='digital_card'
    )
    
    # Card identification
    card_number = models.CharField(
        max_length=16,  # Updated to support 16-digit card numbers
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
    
    # Card type identifier
    card_type = models.CharField(
        max_length=10,
        default='DIGITAL',
        editable=False
    )
    
    # Add QR image field
    qr_image = models.ImageField(
        upload_to='qr_codes/',
        blank=True,
        null=True,
        help_text='Generated QR code image with logo'
    )
    
    # Add template field
    template = models.ForeignKey(
        'PhysicalCardTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Card design template to use instead of the default.'
    )

    class Meta:
        verbose_name = 'Digital Card'
        verbose_name_plural = 'Digital Cards'
        ordering = ['-issued_date']
    
    def __str__(self):
        return f"Digital Card #{self.card_number} - {self.user.get_full_name()}"
    
    def generate_luhn_check_digit(self, partial_number):
        """Generate Luhn algorithm check digit for card validation"""
        # Convert to list of integers
        digits = [int(d) for d in partial_number]
        
        for i in range(len(digits) - 1, -1, -2):  # Double every second digit from the right
            doubled_digit = digits[i] * 2
            if doubled_digit > 9:
                digits[i] = doubled_digit - 9
            else:
                digits[i] = doubled_digit

        total_sum = sum(digits)
        check_digit = (10 - (total_sum % 10)) % 10

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
        import logging
        logger = logging.getLogger(__name__)

        while True:
            # Generate 15 digits: 2 (SAFA prefix) + YYYY (year) + 10 random digits
            year = timezone.now().year
            prefix = "2"  # SAFA prefix
            random_part = get_random_string(10, allowed_chars='0123456789')

            # Combine to get 15 digits (without check digit)
            partial_number = f"{prefix}{year}{random_part}"
            logger.info(f"Partial card number (15 digits): {partial_number}")

            # Generate the check digit using Luhn algorithm
            check_digit = self.generate_luhn_check_digit(partial_number)
            logger.info(f"Generated check digit: {check_digit}")

            # Create the 16-digit card number
            card_number = f"{partial_number}{check_digit}"
            logger.info(f"Final card number (16 digits): {card_number}")

            # Validate uniqueness in the database
            if not DigitalCard.objects.filter(card_number=card_number).exists():
                self.card_number = card_number
                break

    def generate_qr_data(self):
        """Generate optimized QR code data with size limits"""
        import json
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
            'n': f"{self.user.first_name} {self.user.last_name}"[:30],  # Limit name length
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
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Generated QR data for card {self.card_number}: length={len(signed_data)}")
        
        # Ensure data size is reasonable
        if len(self.qr_code_data) > 1500:  # Safety limit
            # Fallback to minimal data
            minimal_data = {
                'id': str(self.card_uuid)[:8],
                'u': self.user.id,
                's': self.user.safa_id,
                'exp': self.expires_date.strftime('%Y%m%d'),
            }
            self.qr_code_data = signing.dumps(minimal_data)

    def generate_qr_image(self):
        """Generate QR code image with SAFA logo and profile picture"""
        try:
            import logging
            logger = logging.getLogger(__name__)

            # Ensure we have QR data first
            if not self.qr_code_data:
                self.generate_qr_data()

            logger.info(f"Generating QR image for card {self.card_number} with data length: {len(self.qr_code_data)}")

            # Get SAFA logo path from static files
            logo_path = None
            possible_paths = [
                os.path.join(settings.BASE_DIR, 'static', 'images', 'default_logo.png'),
                os.path.join(settings.STATICFILES_DIRS[0], 'images', 'default_logo.png') if settings.STATICFILES_DIRS else None,
                os.path.join(settings.STATIC_ROOT, 'images', 'default_logo.png') if settings.STATIC_ROOT else None,
            ]

            for path in possible_paths:
                if path and os.path.exists(path):
                    logo_path = path
                    break

            # Generate QR image with SAFA branding
            qr_img = generate_qr_with_logo(
                qr_data=self.qr_code_data,  # Use the encrypted data, not card number
                logo_path=logo_path,
                profile_image=None,  # Skip profile for now to avoid scan issues
                size=400
            )

            # Save QR image
            from .qr_generator import save_qr_image
            filename = f"qr_{self.card_number}_{self.qr_code_version}.png"
            self.qr_image = save_qr_image(qr_img, filename)

            logger.info(f"QR image saved successfully for card {self.card_number}")
            return True

        except Exception as e:
            logger.error(f"Failed to generate QR image for card {self.card_number}: {str(e)}")
            return False

    def get_qr_base64(self):
        """Get QR code as base64 for web display"""
        try:
            if self.qr_image:
                with open(self.qr_image.path, 'rb') as img_file:
                    import base64
                    img_str = base64.b64encode(img_file.read()).decode()
                    return f"data:image/png;base64,{img_str}"
            else:
                raise FileNotFoundError("QR image file not found")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to convert QR image to base64: {str(e)}")
        return None
    
    def is_valid(self):
        """Check if card is currently valid"""
        return (
            self.status == 'ACTIVE' and 
            self.expires_date >= timezone.now().date()
        )
    
    def is_card_number_valid(self):
        """Check if the card number is valid using Luhn algorithm"""
        return self.verify_luhn_algorithm(self.card_number)

    def save(self, *args, **kwargs):
        """Override save method to log card number before saving"""
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"Saving DigitalCard with card number: {self.card_number}")
        
        # Generate card number if not set
        if not self.card_number:
            self.generate_card_number()
        
        # Set expiry date from user's membership if not set
        if not self.expires_date and self.user.membership_expires_date:
            self.expires_date = self.user.membership_expires_date
        
        # Generate QR code data
        self.generate_qr_data()
        
        # Save first to get an ID
        super().save(*args, **kwargs)
        
        # Generate QR image after saving (avoid recursion issues)
        if not self.qr_image:
            self.generate_qr_image()
            # Update only the qr_image field to avoid infinite recursion
            if self.qr_image:
                DigitalCard.objects.filter(pk=self.pk).update(qr_image=self.qr_image)

class PhysicalCard(models.Model):
    """Physical membership card model"""
    
    PRINT_STATUS_CHOICES = [
        ('PENDING', 'Pending Print'),
        ('PRINTED', 'Printed'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled')
    ]
    
    # Link to user
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='physical_card'
    )
    
    # Card identification (same as digital for consistency)
    card_number = models.CharField(
        max_length=12,
        help_text='Same as digital card number'
    )
    
    # Print and shipping status
    print_status = models.CharField(
        max_length=20,
        choices=PRINT_STATUS_CHOICES,
        default='PENDING'
    )
    ordered_date = models.DateTimeField(auto_now_add=True)
    printed_date = models.DateTimeField(null=True, blank=True)
    shipped_date = models.DateTimeField(null=True, blank=True)
    delivered_date = models.DateTimeField(null=True, blank=True)
    
    # Shipping information
    shipping_address = models.TextField(
        help_text='Address for card delivery'
    )
    tracking_number = models.CharField(
        max_length=50,
        blank=True,
        help_text='Shipping tracking number'
    )
    
    # Card type identifier
    card_type = models.CharField(
        max_length=10,
        default='PHYSICAL',
        editable=False
    )
    
    # Add template field
    template = models.ForeignKey(
        'PhysicalCardTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Card design template'
    )
    
    class Meta:
        verbose_name = 'Physical Card'
        verbose_name_plural = 'Physical Cards'
        ordering = ['-ordered_date']
    
    def __str__(self):
        return f"Physical Card #{self.card_number} - {self.user.get_full_name()} ({self.print_status})"
    
    def save(self, *args, **kwargs):
        # Set card number from digital card if exists
        if not self.card_number and hasattr(self.user, 'digital_card'):
            self.card_number = self.user.digital_card.card_number
        
        super().save(*args, **kwargs)

class PhysicalCardTemplate(models.Model):
    """Template for physical card design"""
    
    TEMPLATE_TYPES = [
        ('STANDARD', 'Standard Member Card'),
        ('OFFICIAL', 'Official/Admin Card'),
        ('PLAYER', 'Player Card'),
        ('COACH', 'Coach Card'),
        ('REFEREE', 'Referee Card'),
        ('EXECUTIVE', 'Executive Card'),
    ]
    
    name = models.CharField(max_length=100, help_text='Template name')
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES, default='STANDARD')
    
    # Card dimensions and design
    card_front_image = models.ImageField(
        upload_to='card_templates/front/',
        help_text='Front side template image'
    )
    card_back_image = models.ImageField(
        upload_to='card_templates/back/',
        blank=True,
        null=True,
        help_text='Back side template image (optional)'
    )
    
    # Field positions for dynamic data (coordinates in pixels)
    name_position_x = models.IntegerField(default=50)
    name_position_y = models.IntegerField(default=100)
    photo_position_x = models.IntegerField(default=20)
    photo_position_y = models.IntegerField(default=20)
    qr_position_x = models.IntegerField(default=200)
    qr_position_y = models.IntegerField(default=150)
    
    # Card specifications
    card_width = models.IntegerField(default=856, help_text='Card width in pixels (300 DPI)')
    card_height = models.IntegerField(default=540, help_text='Card height in pixels (300 DPI)')
    
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Physical Card Template'
        verbose_name_plural = 'Physical Card Templates'
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"