from rest_framework import serializers
from .models import CustomUser

class MCPUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'role', 'date_of_birth',
            'gender', 'nationality', 'membership_status', 'membership_paid_date',
            'membership_activated_date', 'membership_expires_date',
            'membership_fee_amount', 'card_delivery_preference',
            'physical_card_requested', 'physical_card_delivery_address',
            'employment_status', 'position', 'supporting_club', 'club',
            'organization_type', 'profile_photo', 'registration_date',
        ]
        read_only_fields = ['id', 'membership_status', 'membership_paid_date', 'membership_activated_date', 'membership_expires_date']

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'
