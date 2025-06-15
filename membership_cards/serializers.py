from rest_framework import serializers
from .models import DigitalCard

class DigitalCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = DigitalCard
        fields = '__all__'
