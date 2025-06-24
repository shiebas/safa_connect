from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Count, Q, F
from datetime import timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Stadium, SeatMap, InternationalMatch, Ticket, TicketGroup
from .serializers import (
    StadiumSerializer, SeatMapSerializer, InternationalMatchSerializer,
    TicketSerializer, TicketGroupSerializer
)
from supporters.models import SupporterProfile
from membership.models.invoice import Invoice
from membership.models import Member
from geography.models import Club


def create_ticket_invoice(ticket, match, supporter):
    """Create an invoice for a ticket purchase"""
    try:
        # Calculate tax (15% VAT)
        tax_amount = ticket.final_price * 0.15
        total_amount = ticket.final_price + tax_amount
        
        # Generate invoice number
        invoice_number = f"TKT-{timezone.now().strftime('%Y%m%d')}-{ticket.id.hex[:8].upper()}"
        
        # Get a default club (first available club)
        default_club = Club.objects.first()
        club_to_use = supporter.favorite_club or default_club
        
        if not club_to_use:
            print("No club available for invoice creation")
            return None
        
        # Get or create a system member for issuing invoices
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        system_user, created = User.objects.get_or_create(
            email='system@safa.net',
            defaults={
                'username': 'system',
                'first_name': 'System',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_active': True
            }
        )
        
        # Get or create system member
        system_member, created = Member.objects.get_or_create(
            user=system_user,
            defaults={
                'membership_status': 'ACTIVE',
                'role': 'ADMIN_SYSTEM'
            }
        )
        
        # Create invoice
        invoice = Invoice.objects.create(
            invoice_number=invoice_number,
            invoice_type='TICKET',
            amount=total_amount,
            tax_amount=tax_amount,
            status='PENDING',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=7),  # 7 days for ticket payment
            club=club_to_use,
            issued_by=system_member,
            notes=f"International Match Ticket - {match.name}"
        )
        
        return invoice
        
    except Exception as e:
        print(f"Error creating invoice: {e}")
        return None


@staff_member_required
def events_dashboard(request):
    """Events dashboard for administrators"""
    # Upcoming matches
    upcoming_matches = InternationalMatch.objects.filter(
        match_date__gte=timezone.now(),
        is_active=True
    ).order_by('match_date')[:5]
    
    # Recent ticket sales
    recent_tickets = Ticket.objects.filter(
        purchased_at__gte=timezone.now() - timedelta(days=7)
    ).order_by('-purchased_at')[:10]
    
    # Statistics
    total_matches = InternationalMatch.objects.filter(is_active=True).count()
    total_tickets_sold = Ticket.objects.filter(status__in=['PAID', 'USED']).count()
    total_revenue = Ticket.objects.filter(status__in=['PAID', 'USED']).aggregate(
        total=Sum('final_price')
    )['total'] or 0
    
    # Active stadiums
    active_stadiums = Stadium.objects.filter(is_active=True).count()
    
    context = {
        'upcoming_matches': upcoming_matches,
        'recent_tickets': recent_tickets,
        'total_matches': total_matches,
        'total_tickets_sold': total_tickets_sold,
        'total_revenue': total_revenue,
        'active_stadiums': active_stadiums,
    }
    
    return render(request, 'events/dashboard.html', context)


@login_required
def available_matches(request):
    """List available matches for ticket purchase"""
    now = timezone.now()
    
    # Get matches with open sales
    matches = InternationalMatch.objects.filter(
        is_active=True,
        sales_open_date__lte=now,
        sales_close_date__gte=now,
        match_date__gte=now
    ).exclude(
        tickets_sold__gte=F('tickets_available')
    ).order_by('match_date')
    
    context = {
        'matches': matches,
    }
    
    return render(request, 'events/available_matches.html', context)


@login_required
def match_detail(request, match_id):
    """Detailed view of a match for ticket selection"""
    match = get_object_or_404(InternationalMatch, id=match_id, is_active=True)
    
    # Check if sales are open
    now = timezone.now()
    if now < match.sales_open_date:
        messages.warning(request, 'Ticket sales have not opened yet.')
        return redirect('events:available_matches')
    
    if now > match.sales_close_date:
        messages.warning(request, 'Ticket sales have closed.')
        return redirect('events:available_matches')
    
    # Get available seats by price tier
    available_seats = match.stadium.seats.filter(
        is_active=True
    ).exclude(
        id__in=Ticket.objects.filter(
            match=match,
            status__in=['RESERVED', 'PAID', 'USED']
        ).values_list('seat_id', flat=True)
    ).order_by('price_tier', 'section', 'row', 'seat_number')
    
    # Group by price tier
    seats_by_tier = {}
    for seat in available_seats:
        if seat.price_tier not in seats_by_tier:
            seats_by_tier[seat.price_tier] = []
        
        # Calculate final price with discounts
        final_price = seat.base_price
        if match.is_early_bird_active:
            final_price = final_price * (1 - match.early_bird_discount / 100)
        
        seats_by_tier[seat.price_tier].append({
            'seat': seat,
            'final_price': final_price
        })
    
    context = {
        'match': match,
        'seats_by_tier': seats_by_tier,
        'is_early_bird': match.is_early_bird_active,
    }
    
    return render(request, 'events/match_detail.html', context)


# API ViewSets
class StadiumViewSet(viewsets.ModelViewSet):
    queryset = Stadium.objects.all()
    serializer_class = StadiumSerializer
    
    @action(detail=True, methods=['get'])
    def seats(self, request, pk=None):
        stadium = self.get_object()
        seats = stadium.seats.filter(is_active=True)
        serializer = SeatMapSerializer(seats, many=True)
        return Response(serializer.data)


class InternationalMatchViewSet(viewsets.ModelViewSet):
    queryset = InternationalMatch.objects.all()
    serializer_class = InternationalMatchSerializer
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        matches = self.queryset.filter(
            match_date__gte=timezone.now(),
            is_active=True
        ).order_by('match_date')
        serializer = self.get_serializer(matches, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def available_seats(self, request, pk=None):
        match = self.get_object()
        available_seats = match.stadium.seats.filter(
            is_active=True
        ).exclude(
            id__in=Ticket.objects.filter(
                match=match,
                status__in=['RESERVED', 'PAID', 'USED']
            ).values_list('seat_id', flat=True)
        )
        serializer = SeatMapSerializer(available_seats, many=True)
        return Response(serializer.data)


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer


class TicketGroupViewSet(viewsets.ModelViewSet):
    queryset = TicketGroup.objects.all()
    serializer_class = TicketGroupSerializer
