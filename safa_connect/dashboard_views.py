from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from events.models import Stadium, InternationalMatch, Ticket, TicketGroup
from supporters.models import SupporterProfile
from membership.models import Invoice
from membership.models import Member
from geography.models import Club
from accounts.models import CustomUser


@staff_member_required
def superuser_dashboard(request):
    """Comprehensive superuser dashboard showing all key metrics"""
    
    # Time ranges for analytics
    now = timezone.now()
    last_7_days = now - timedelta(days=7)
    last_30_days = now - timedelta(days=30)
    
    # ==== EVENTS & TICKETING METRICS ====
    events_metrics = {
        'total_stadiums': Stadium.objects.filter(is_active=True).count(),
        'total_matches': InternationalMatch.objects.filter(is_active=True).count(),
        'upcoming_matches': InternationalMatch.objects.filter(
            match_date__gte=now, is_active=True
        ).count(),
        'total_tickets_sold': Ticket.objects.filter(status__in=['PAID', 'USED']).count(),
        'tickets_revenue': Ticket.objects.filter(status__in=['PAID', 'USED']).aggregate(
            total=Sum('final_price')
        )['total'] or 0,
        'recent_ticket_sales': Ticket.objects.filter(
            purchased_at__gte=last_7_days
        ).count(),
    }
    
    # Top selling matches
    top_matches = InternationalMatch.objects.annotate(
        sold_count=Count('tickets', filter=Q(tickets__status__in=['PAID', 'USED']))
    ).filter(sold_count__gt=0).order_by('-sold_count')[:5]
    
    # Recent ticket sales
    recent_tickets = Ticket.objects.filter(
        purchased_at__gte=last_7_days
    ).select_related('match', 'supporter__user', 'seat').order_by('-purchased_at')[:10]
    
    # ==== SUPPORTERS METRICS ====
    supporters_metrics = {
        'total_supporters': SupporterProfile.objects.count(),
        'verified_supporters': SupporterProfile.objects.filter(is_verified=True).count(),
        'new_supporters_7days': SupporterProfile.objects.filter(
            created_at__gte=last_7_days
        ).count(),
        'supporters_with_location': SupporterProfile.objects.filter(
            latitude__isnull=False, longitude__isnull=False
        ).count(),
    }
    
    # Supporters by membership type
    supporters_by_type = SupporterProfile.objects.values('membership_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Supporters by province
    supporters_by_province = SupporterProfile.objects.values('location_province').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # ==== INVOICES & REVENUE METRICS ====
    invoice_metrics = {
        'total_invoices': Invoice.objects.count(),
        'pending_invoices': Invoice.objects.filter(status='PENDING').count(),
        'paid_invoices': Invoice.objects.filter(status='PAID').count(),
        'total_revenue': Invoice.objects.filter(status='PAID').aggregate(
            total=Sum('amount')
        )['total'] or 0,
        'recent_revenue_7days': Invoice.objects.filter(
            status='PAID', 
            payment_date__gte=last_7_days
        ).aggregate(total=Sum('amount'))['total'] or 0,
    }
    
    # Invoice breakdown by type
    invoice_by_type = Invoice.objects.values('invoice_type').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    ).order_by('-total_amount')
    
    # Recent invoices
    recent_invoices = Invoice.objects.filter(
        created__gte=last_7_days
    ).order_by('-created')[:10]
    
    # ==== MEMBERSHIP METRICS ====
    membership_metrics = {
        'total_members': Member.objects.count(),
        'active_members': Member.objects.filter(status='ACTIVE').count(),
        'total_players': Member.objects.filter(role='PLAYER').count(),
        'total_clubs': Club.objects.count(),
        'total_users': CustomUser.objects.count(),
    }
    
    # ==== RECENT ACTIVITY ====
    # Get recent activities across all modules
    recent_activities = []
    
    # Recent supporter registrations
    for supporter in SupporterProfile.objects.filter(
        created_at__gte=last_7_days
    ).select_related('user')[:5]:
        recent_activities.append({
            'type': 'supporter_registration',
            'title': f'New Supporter: {supporter.user.get_full_name()}',
            'subtitle': f'{supporter.get_membership_type_display()}',
            'timestamp': supporter.created_at,
            'icon': 'bi-people-fill',
            'color': 'success'
        })
    
    # Recent ticket purchases
    for ticket in Ticket.objects.filter(
        purchased_at__gte=last_7_days
    ).select_related('match', 'supporter__user')[:5]:
        recent_activities.append({
            'type': 'ticket_purchase',
            'title': f'Ticket Purchase: {ticket.match.name}',
            'subtitle': f'By {ticket.supporter.user.get_full_name()}',
            'timestamp': ticket.purchased_at,
            'icon': 'bi-ticket-perforated-fill',
            'color': 'primary'
        })
    
    # Recent invoice payments
    for invoice in Invoice.objects.filter(
        status='PAID',
        payment_date__gte=last_7_days
    )[:5]:
        recent_activities.append({
            'type': 'invoice_payment',
            'title': f'Payment Received: {invoice.invoice_number}',
            'subtitle': f'R {invoice.amount:,.2f}',
            'timestamp': invoice.payment_date,
            'icon': 'bi-credit-card-fill',
            'color': 'warning'
        })
    
    # Sort activities by timestamp
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:15]  # Limit to 15 most recent
    
    context = {
        'events_metrics': events_metrics,
        'supporters_metrics': supporters_metrics,
        'invoice_metrics': invoice_metrics,
        'membership_metrics': membership_metrics,
        'top_matches': top_matches,
        'recent_tickets': recent_tickets,
        'supporters_by_type': supporters_by_type,
        'supporters_by_province': supporters_by_province,
        'invoice_by_type': invoice_by_type,
        'recent_invoices': recent_invoices,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'admin/superuser_dashboard.html', context)
