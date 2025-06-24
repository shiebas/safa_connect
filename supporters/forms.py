from django import forms
from .models import SupporterProfile, SupporterPreferences

class SupporterPreferencesForm(forms.ModelForm):
    """Form for supporter preferences matrix"""
    class Meta:
        model = SupporterPreferences
        exclude = ['created_at', 'updated_at']
        widgets = {
            'communication_frequency': forms.Select(
                attrs={'class': 'form-select'}
            ),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Group fields by category for better display
        self.field_categories = {
            'Tickets & Events': [
                'discount_tickets', 'vip_experiences', 'international_matches', 
                'local_matches', 'youth_matches'
            ],
            'Merchandise & Retail': [
                'official_jerseys', 'casual_clothing', 'limited_editions', 'seasonal_sales'
            ],
            'Travel & Hospitality': [
                'match_travel_packages', 'accommodation_deals', 'transport_offers', 'international_tours'
            ],
            'Digital & Media': [
                'exclusive_content', 'player_interviews', 'live_streaming', 'podcasts_videos'
            ],
            'Community & Events': [
                'community_events', 'coaching_clinics', 'player_meetups', 'charity_initiatives'
            ],
            'Food & Beverage': [
                'stadium_dining', 'partner_restaurant_deals', 'catering_packages'
            ],
            'Financial Services': [
                'insurance_products', 'banking_offers', 'investment_opportunities'
            ],
            'Communication Preferences': [
                'email_notifications', 'sms_alerts', 'push_notifications', 'whatsapp_updates',
                'communication_frequency'
            ],
            'Special Interests': [
                'youth_development', 'womens_football', 'disability_football', 
                'referee_programs', 'coaching_development'
            ]
        }
        
        # Add CSS classes to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})

class SupporterRegistrationForm(forms.ModelForm):
    # Add preferences selection
    setup_preferences = forms.BooleanField(
        required=False,
        initial=True,
        label="Set up my marketing preferences now",
        help_text="You can customize what updates you'd like to receive from SAFA",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = SupporterProfile
        fields = [
            'favorite_club', 'membership_type', 'id_number', 'id_document',
            'date_of_birth', 'address', 'latitude', 'longitude', 
            'location_city', 'location_province', 'location_country',
            'location_accuracy'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            ),
            'id_number': forms.TextInput(
                attrs={
                    'placeholder': 'Enter your South African ID number',
                    'class': 'form-control'
                }
            ),
            'address': forms.Textarea(
                attrs={
                    'rows': 3,
                    'placeholder': 'Enter your full address (or use location detection)',
                    'class': 'form-control'
                }
            ),
            'favorite_club': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),
            'membership_type': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),
            'id_document': forms.FileInput(
                attrs={
                    'class': 'form-control',
                    'accept': '.pdf,.jpg,.jpeg,.png'
                }
            ),
            # Hidden fields for geolocation data
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'location_city': forms.HiddenInput(),
            'location_province': forms.HiddenInput(),
            'location_country': forms.HiddenInput(),
            'location_accuracy': forms.HiddenInput(),
        }
        
        labels = {
            'favorite_club': 'Favorite Club',
            'membership_type': 'Membership Type',
            'id_number': 'ID Number',
            'id_document': 'ID Document',
            'date_of_birth': 'Date of Birth',
            'address': 'Address'
        }
        
        help_texts = {
            'favorite_club': 'Select the club you support (optional)',
            'membership_type': 'Choose your membership level',
            'id_number': 'Your South African ID number for verification',
            'id_document': 'Upload a clear photo or scan of your ID document',
            'date_of_birth': 'Your date of birth',
            'address': 'Your full residential address'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make favorite_club optional by adding empty choice
        if 'favorite_club' in self.fields:
            self.fields['favorite_club'].empty_label = "Select a club (optional)"
        
        # Set required fields
        required_fields = ['membership_type']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
