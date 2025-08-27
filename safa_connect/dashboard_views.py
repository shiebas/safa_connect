from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from django.contrib.sessions.models import Session
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
    
    # ==== ONLINE USERS ====
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    user_ids = []
    for session in sessions:
        session_data = session.get_decoded()
        user_id = session_data.get('_auth_user_id')
        if user_id:
            user_ids.append(user_id)
    
    online_users = CustomUser.objects.filter(id__in=user_ids).select_related('province', 'region')

    # ==== INVOICES & REVENUE METRICS ====
    invoice_metrics = {
        'total_invoices': Invoice.objects.count(),
        'pending_invoices': Invoice.objects.filter(status='PENDING').count(),
        'paid_invoices': Invoice.objects.filter(status='PAID').count(),
        'total_revenue': Invoice.objects.filter(status='PAID').aggregate(
            total=Sum('total_amount')
        )['total'] or 0,
        'recent_revenue_7days': Invoice.objects.filter(
            status='PAID', 
            payment_date__gte=last_7_days
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
    }
    
    # Invoice breakdown by type
    invoice_by_type = Invoice.objects.values('invoice_type').annotate(
        count=Count('id'),
        total_amount=Sum('total_amount')
    ).order_by('-total_amount')
    
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
    
    # Recent invoice payments
    for invoice in Invoice.objects.filter(
        status='PAID',
        payment_date__gte=last_7_days
    )[:5]:
        recent_activities.append({
            'type': 'invoice_payment',
            'title': f'Payment Received: {invoice.invoice_number}',
            'subtitle': f'R {invoice.total_amount:,.2f}',
            'timestamp': invoice.payment_date,
            'icon': 'bi-credit-card-fill',
            'color': 'warning'
        })
    
    # Sort activities by timestamp
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:15]  # Limit to 15 most recent
    
    # ==== PENDING APPROVALS ====
    pending_approvals = CustomUser.objects.filter(membership_status='PENDING').order_by('-registration_date')

    context = {
        'online_users': online_users,
        'invoice_metrics': invoice_metrics,
        'membership_metrics': membership_metrics,
        'invoice_by_type': invoice_by_type,
        'recent_activities': recent_activities,
        'pending_approvals': pending_approvals,
    }
    
    return render(request, 'admin/superuser_dashboard.html', context)
