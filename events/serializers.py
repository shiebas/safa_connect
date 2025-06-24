from rest_framework import serializers
from .models import Stadium, SeatMap, InternationalMatch, Ticket, TicketGroup


class StadiumSerializer(serializers.ModelSerializer):
    seat_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Stadium
        fields = '__all__'
    
    def get_seat_count(self, obj):
        return obj.seats.count()


class SeatMapSerializer(serializers.ModelSerializer):
    stadium_name = serializers.CharField(source='stadium.name', read_only=True)
    
    class Meta:
        model = SeatMap
        fields = '__all__'


class InternationalMatchSerializer(serializers.ModelSerializer):
    stadium_name = serializers.CharField(source='stadium.name', read_only=True)
    tickets_remaining = serializers.ReadOnlyField()
    sales_status = serializers.ReadOnlyField()
    is_early_bird_active = serializers.ReadOnlyField()
    
    class Meta:
        model = InternationalMatch
        fields = '__all__'


class TicketSerializer(serializers.ModelSerializer):
    match_name = serializers.CharField(source='match.name', read_only=True)
    supporter_name = serializers.CharField(source='supporter.user.get_full_name', read_only=True)
    seat_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Ticket
        fields = '__all__'
    
    def get_seat_info(self, obj):
        return f"{obj.seat.section}{obj.seat.row}-{obj.seat.seat_number}"


class TicketGroupSerializer(serializers.ModelSerializer):
    match_name = serializers.CharField(source='match.name', read_only=True)
    primary_contact_name = serializers.CharField(source='primary_contact.user.get_full_name', read_only=True)
    
    class Meta:
        model = TicketGroup
        fields = '__all__'
