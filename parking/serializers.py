from rest_framework import serializers
from .models import ParkingZone, ParkingSpace, ParkingAllocation

class ParkingZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingZone
        fields = '__all__'

class ParkingSpaceSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source='zone.name', read_only=True)

    class Meta:
        model = ParkingSpace
        fields = '__all__'

class ParkingAllocationSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    space_details = ParkingSpaceSerializer(source='space', read_only=True)
    event_name = serializers.CharField(source='event.name', read_only=True)

    class Meta:
        model = ParkingAllocation
        fields = '__all__'
