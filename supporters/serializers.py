from rest_framework import serializers
from .models import SupporterProfile

class SupporterProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupporterProfile
        fields = '__all__'
