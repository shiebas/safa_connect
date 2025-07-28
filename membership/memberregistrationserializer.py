from rest_framework import serializers
from .models import MemberRegistration
from django.utils.translation import gettext_lazy as _

class MemberRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberRegistration
        fields = [
            'id', 'member', 'club', 'registration_date', 'status',
            'member_status', 'season_config', 'registered_by_admin',
            'registering_admin', 'province', 'region', 'lfa',
            'national_federation', 'association', 'emergency_contact',
            'emergency_phone', 'medical_notes', 'position', 'jersey_number',
            'notes'
        ]

    def create(self, validated_data):
        # Custom logic for creating a registration
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Custom logic for updating a registration
        return super().update(instance, validated_data)
