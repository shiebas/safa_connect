# membership/admin_views.py - CORRECTED VERSION
# Fixed to work with the new SAFA models

from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta

# Import the corrected models
from .models import (
    Member, Transfer, Invoice, SAFASeasonConfig, SAFAFeeStructure,
    RegistrationWorkflow, ClubMemberQuota, MemberSeasonHistory
)

# Try to import existing models if they exist

def is_safa_admin(user):
    """Check if user has SAFA admin privileges"""
    return (
        user.is_superuser or 
        getattr(user, 'role', None) in ['ADMIN_NATIONAL', 'ADMIN_NATIONAL_ACCOUNTS']
    )


@staff_member_required
@user_passes_test(is_safa_admin)
def national_admin_dashboard(request):
    """Dashboard view for National Admins"""
    
    # Get current season
    active_season = SAFASeasonConfig.get_active_season()
    
    # Basic statistics
    total_members = Member.objects.count()
    pending_members = Member.objects.filter(status='PENDING').count()
    active_members = Member.objects.filter(status='ACTIVE').count()
    
    # Transfer statistics
    pending_transfers = Transfer.objects.filter(status='PENDING').count()
    total_transfers = Transfer.objects.count()
    
    # Invoice statistics
    overdue_invoices = Invoice.objects.filter(status='OVERDUE').count()
    pending_invoices = Invoice.objects.filter(status='PENDING').count()
    total_invoices = Invoice.objects.count()
    
    # Revenue statistics
    total_revenue = Invoice.objects.filter(status='PAID').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    outstanding_revenue = Invoice.objects.filter(
        status__in=['PENDING', 'OVERDUE']
    ).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Registration workflow statistics
    incomplete_registrations = RegistrationWorkflow.objects.filter(
        completion_percentage__lt=100
    ).count()
    
    # Recent activity (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_members = Member.objects.filter(created__gte=thirty_days_ago).count()
    recent_invoices = Invoice.objects.filter(created__gte=thirty_days_ago).count()
    
    # Member breakdown by role
    member_breakdown = Member.objects.values('role').annotate(
        count=Count('id')
    ).order_by('role')
    
    # Club statistics
    club_stats = ClubMemberQuota.objects.filter(
        season_config=active_season
    ).aggregate(
        total_clubs=Count('club', distinct=True),
        total_capacity=Sum('max_senior_players') + Sum('max_junior_players'),
        total_registered=Sum('current_senior_players') + Sum('current_junior_players')
    ) if active_season else {}
    
    # Seasonal statistics
    seasonal_stats = {}
    if active_season:
        seasonal_stats = {
            'season_year': active_season.season_year,
            'season_members': Member.objects.filter(current_season=active_season).count(),
            'season_revenue': Invoice.objects.filter(
                season_config=active_season,
                status='PAID'
            ).aggregate(total=Sum('total_amount'))['total'] or 0,
            'season_outstanding': Invoice.objects.filter(
                season_config=active_season,
                status__in=['PENDING', 'OVERDUE']
            ).aggregate(total=Sum('total_amount'))['total'] or 0,
        }
    
    # Recent members for quick review
    recent_member_list = Member.objects.filter(
        status='PENDING'
    ).order_by('-created')[:10]
    
    # Overdue invoices for attention
    overdue_invoice_list = Invoice.objects.filter(
        status='OVERDUE'
    ).order_by('due_date')[:10]
    
    context = {
        'title': _("SAFA National Admin Dashboard"),
        'active_season': active_season,
        
        # Member statistics
        'total_members': total_members,
        'pending_members': pending_members,
        'active_members': active_members,
        'recent_members': recent_members,
        'member_breakdown': member_breakdown,
        'recent_member_list': recent_member_list,
        
        # Transfer statistics
        'pending_transfers': pending_transfers,
        'total_transfers': total_transfers,
        
        # Financial statistics
        'overdue_invoices': overdue_invoices,
        'pending_invoices': pending_invoices,
        'total_invoices': total_invoices,
        'recent_invoices': recent_invoices,
        'total_revenue': total_revenue,
        'outstanding_revenue': outstanding_revenue,
        'overdue_invoice_list': overdue_invoice_list,
        
        # Registration statistics
        'incomplete_registrations': incomplete_registrations,
        
        # Club statistics
        'club_stats': club_stats,
        
        # Seasonal statistics
        'seasonal_stats': seasonal_stats,
    }
    
    return render(request, 'admin/membership/dashboard_national_admin.html', context)


@staff_member_required
@user_passes_test(is_safa_admin)
def financial_dashboard(request):
    """Dashboard view for Financial Overview"""
    
    active_season = SAFASeasonConfig.get_active_season()
    
    # Financial overview
    financial_summary = {
        'total_invoiced': Invoice.objects.aggregate(total=Sum('total_amount'))['total'] or 0,
        'total_paid': Invoice.objects.filter(status='PAID').aggregate(total=Sum('total_amount'))['total'] or 0,
        'total_outstanding': Invoice.objects.filter(
            status__in=['PENDING', 'OVERDUE']
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
        'overdue_amount': Invoice.objects.filter(status='OVERDUE').aggregate(
            total=Sum('total_amount')
        )['total'] or 0,
    }
    
    # Payment collection rate
    if financial_summary['total_invoiced'] > 0:
        collection_rate = (financial_summary['total_paid'] / financial_summary['total_invoiced']) * 100
    else:
        collection_rate = 0
    
    # Revenue by entity type
    revenue_breakdown = Invoice.objects.filter(
        status='PAID'
    ).values('invoice_type').annotate(
        total=Sum('total_amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Monthly revenue trend (last 12 months)
    monthly_revenue = []
    for i in range(12):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start.replace(day=28) + timedelta(days=4)
        month_end = month_end.replace(day=1) - timedelta(days=1)
        
        revenue = Invoice.objects.filter(
            status='PAID',
            payment_date__range=[month_start, month_end]
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        monthly_revenue.append({
            'month': month_start.strftime('%b %Y'),
            'revenue': revenue
        })
    
    monthly_revenue.reverse()
    
    # Fee structure overview
    fee_structures = []
    if active_season:
        fee_structures = SAFAFeeStructure.objects.filter(
            season_config=active_season
        ).order_by('entity_type')
    
    # Outstanding invoices by age
    today = timezone.now().date()
    overdue_breakdown = {
        '0-30_days': Invoice.objects.filter(
            status='OVERDUE',
            due_date__gte=today - timedelta(days=30)
        ).count(),
        '31-60_days': Invoice.objects.filter(
            status='OVERDUE',
            due_date__range=[today - timedelta(days=60), today - timedelta(days=31)]
        ).count(),
        '61-90_days': Invoice.objects.filter(
            status='OVERDUE',
            due_date__range=[today - timedelta(days=90), today - timedelta(days=61)]
        ).count(),
        'over_90_days': Invoice.objects.filter(
            status='OVERDUE',
            due_date__lt=today - timedelta(days=90)
        ).count(),
    }
    
    context = {
        'title': _("SAFA Financial Dashboard"),
        'active_season': active_season,
        'financial_summary': financial_summary,
        'collection_rate': collection_rate,
        'revenue_breakdown': revenue_breakdown,
        'monthly_revenue': monthly_revenue,
        'fee_structures': fee_structures,
        'overdue_breakdown': overdue_breakdown,
    }
    
    return render(request, 'admin/membership/dashboard_financial.html', context)


@staff_member_required
@user_passes_test(is_safa_admin)
def member_statistics(request):
    """Detailed member statistics view"""
    
    active_season = SAFASeasonConfig.get_active_season()
    
    # Member statistics by status
    status_breakdown = Member.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Member statistics by role
    role_breakdown = Member.objects.values('role').annotate(
        count=Count('id')
    ).order_by('role')
    
    # Member statistics by province
    province_breakdown = Member.objects.values(
        'province__name'
    ).annotate(count=Count('id')).order_by('-count')[:10]
    
    # Age distribution
    age_groups = {
        'Under 18': Member.objects.filter(
            date_of_birth__gt=timezone.now().date() - timedelta(days=18*365)
        ).count(),
        '18-25': Member.objects.filter(
            date_of_birth__range=[
                timezone.now().date() - timedelta(days=25*365),
                timezone.now().date() - timedelta(days=18*365)
            ]
        ).count(),
        '26-35': Member.objects.filter(
            date_of_birth__range=[
                timezone.now().date() - timedelta(days=35*365),
                timezone.now().date() - timedelta(days=26*365)
            ]
        ).count(),
        'Over 35': Member.objects.filter(
            date_of_birth__lt=timezone.now().date() - timedelta(days=35*365)
        ).count(),
    }
    
    # Registration method breakdown
    registration_breakdown = Member.objects.values('registration_method').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Club membership statistics
    club_stats = Member.objects.values('current_club__name').annotate(
        count=Count('id')
    ).order_by('-count')[:20]
    
    # Registration completion statistics
    workflow_stats = RegistrationWorkflow.objects.aggregate(
        complete=Count('id', filter=Q(completion_percentage=100)),
        in_progress=Count('id', filter=Q(completion_percentage__range=[1, 99])),
        not_started=Count('id', filter=Q(completion_percentage=0))
    )
    
    context = {
        'title': _("Member Statistics"),
        'active_season': active_season,
        'status_breakdown': status_breakdown,
        'role_breakdown': role_breakdown,
        'province_breakdown': province_breakdown,
        'age_groups': age_groups,
        'registration_breakdown': registration_breakdown,
        'club_stats': club_stats,
        'workflow_stats': workflow_stats,
    }
    
    return render(request, 'admin/membership/member_statistics.html', context)


@staff_member_required
def season_management(request):
    """Season management dashboard"""
    
    # Only accessible to national admins
    if not is_safa_admin(request.user):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Access denied")
    
    seasons = SAFASeasonConfig.objects.all().order_by('-season_year')
    active_season = SAFASeasonConfig.get_active_season()
    
    # Season statistics
    season_stats = []
    for season in seasons[:5]:  # Last 5 seasons
        stats = {
            'season': season,
            'members': Member.objects.filter(current_season=season).count(),
            'revenue': Invoice.objects.filter(
                season_config=season,
                status='PAID'
            ).aggregate(total=Sum('total_amount'))['total'] or 0,
            'outstanding': Invoice.objects.filter(
                season_config=season,
                status__in=['PENDING', 'OVERDUE']
            ).aggregate(total=Sum('total_amount'))['total'] or 0,
        }
        season_stats.append(stats)
    
    # Current season details
    current_season_details = None
    if active_season:
        current_season_details = {
            'season': active_season,
            'registration_open': active_season.member_registration_open,
            'org_registration_open': active_season.organization_registration_open,
            'days_remaining': (active_season.season_end_date - timezone.now().date()).days,
            'fee_structures': SAFAFeeStructure.objects.filter(season_config=active_season).count(),
        }
    
    context = {
        'title': _("Season Management"),
        'seasons': seasons,
        'active_season': active_season,
        'season_stats': season_stats,
        'current_season_details': current_season_details,
    }
    
    return render(request, 'admin/membership/season_management.html', context)


@staff_member_required
def member_approval_queue(request):
    """Member approval queue for administrators"""
    
    # Filter members based on user role
    user = request.user
    pending_members = Member.objects.filter(status='PENDING')
    
    if not user.is_superuser:
        if getattr(user, 'role', None) == 'ADMIN_PROVINCE' and hasattr(user, 'province'):
            pending_members = pending_members.filter(province=user.province)
        elif getattr(user, 'role', None) == 'ADMIN_REGION' and hasattr(user, 'region'):
            pending_members = pending_members.filter(region=user.region)
        elif getattr(user, 'role', None) == 'ADMIN_LOCAL_FED' and hasattr(user, 'lfa'):
            pending_members = pending_members.filter(lfa=user.lfa)
        elif getattr(user, 'role', None) == 'CLUB_ADMIN' and hasattr(user, 'club'):
            pending_members = pending_members.filter(current_club=user.club)
        else:
            pending_members = pending_members.none()
    
    # Order by registration date (oldest first)
    pending_members = pending_members.order_by('created')
    
    # Group by completion status
    complete_applications = pending_members.filter(registration_complete=True)
    incomplete_applications = pending_members.filter(registration_complete=False)
    
    # Recent approvals and rejections for reference
    recent_approvals = Member.objects.filter(
        status='ACTIVE',
        approved_date__gte=timezone.now() - timedelta(days=7)
    ).order_by('-approved_date')[:10]
    
    recent_rejections = Member.objects.filter(
        status='REJECTED',
        modified__gte=timezone.now() - timedelta(days=7)
    ).order_by('-modified')[:10]
    
    context = {
        'title': _("Member Approval Queue"),
        'pending_members': pending_members,
        'complete_applications': complete_applications,
        'incomplete_applications': incomplete_applications,
        'recent_approvals': recent_approvals,
        'recent_rejections': recent_rejections,
    }
    
    return render(request, 'admin/membership/member_approval_queue.html', context)


@staff_member_required
@user_passes_test(is_safa_admin)
def invoice_management(request):
    """Invoice management dashboard"""
    
    # Invoice statistics
    invoice_stats = {
        'total': Invoice.objects.count(),
        'paid': Invoice.objects.filter(status='PAID').count(),
        'pending': Invoice.objects.filter(status='PENDING').count(),
        'overdue': Invoice.objects.filter(status='OVERDUE').count(),
        'cancelled': Invoice.objects.filter(status='CANCELLED').count(),
    }
    
    # Recent invoices
    recent_invoices = Invoice.objects.order_by('-created')[:20]
    
    # Overdue invoices requiring attention
    overdue_invoices = Invoice.objects.filter(
        status='OVERDUE'
    ).order_by('due_date')[:20]
    
    # Payment trends (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_payments = Invoice.objects.filter(
        status='PAID',
        payment_date__gte=thirty_days_ago
    ).order_by('-payment_date')[:15]
    
    # Invoice aging analysis
    today = timezone.now().date()
    aging_analysis = {
        'current': Invoice.objects.filter(
            status='PENDING',
            due_date__gte=today
        ).count(),
        '1_30_days': Invoice.objects.filter(
            status__in=['PENDING', 'OVERDUE'],
            due_date__range=[today - timedelta(days=30), today - timedelta(days=1)]
        ).count(),
        '31_60_days': Invoice.objects.filter(
            status='OVERDUE',
            due_date__range=[today - timedelta(days=60), today - timedelta(days=31)]
        ).count(),
        '61_90_days': Invoice.objects.filter(
            status='OVERDUE',
            due_date__range=[today - timedelta(days=90), today - timedelta(days=61)]
        ).count(),
        'over_90_days': Invoice.objects.filter(
            status='OVERDUE',
            due_date__lt=today - timedelta(days=90)
        ).count(),
    }
    
    # Revenue by invoice type
    revenue_by_type = Invoice.objects.filter(
        status='PAID'
    ).values('invoice_type').annotate(
        total_revenue=Sum('total_amount'),
        count=Count('id')
    ).order_by('-total_revenue')
    
    context = {
        'title': _("Invoice Management"),
        'invoice_stats': invoice_stats,
        'recent_invoices': recent_invoices,
        'overdue_invoices': overdue_invoices,
        'recent_payments': recent_payments,
        'aging_analysis': aging_analysis,
        'revenue_by_type': revenue_by_type,
    }
    
    return render(request, 'admin/membership/invoice_management.html', context)


@staff_member_required
def transfer_management(request):
    """Transfer management dashboard"""
    
    # Filter transfers based on user role
    user = request.user
    all_transfers = Transfer.objects.all()
    
    if not user.is_superuser:
        if getattr(user, 'role', None) == 'ADMIN_PROVINCE' and hasattr(user, 'province'):
            all_transfers = all_transfers.filter(
                Q(member__province=user.province) |
                Q(from_club__province=user.province) |
                Q(to_club__province=user.province)
            )
        elif getattr(user, 'role', None) == 'CLUB_ADMIN' and hasattr(user, 'club'):
            all_transfers = all_transfers.filter(
                Q(from_club=user.club) | Q(to_club=user.club)
            )
    
    # Transfer statistics
    transfer_stats = {
        'total': all_transfers.count(),
        'pending': all_transfers.filter(status='PENDING').count(),
        'approved': all_transfers.filter(status='APPROVED').count(),
        'rejected': all_transfers.filter(status='REJECTED').count(),
        'cancelled': all_transfers.filter(status='CANCELLED').count(),
    }
    
    # Pending transfers requiring approval
    pending_transfers = all_transfers.filter(
        status='PENDING'
    ).order_by('request_date')
    
    # Recent transfer activity
    recent_transfers = all_transfers.order_by('-request_date')[:15]
    
    # Transfer trends by month
    monthly_transfers = []
    for i in range(6):  # Last 6 months
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start.replace(day=28) + timedelta(days=4)
        month_end = month_end.replace(day=1) - timedelta(days=1)
        
        count = all_transfers.filter(
            request_date__range=[month_start.date(), month_end.date()]
        ).count()
        
        monthly_transfers.append({
            'month': month_start.strftime('%b %Y'),
            'count': count
        })
    
    monthly_transfers.reverse()
    
    # Top clubs by transfer activity
    club_activity = {}
    
    # Outgoing transfers
    outgoing = all_transfers.values('from_club__name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Incoming transfers
    incoming = all_transfers.values('to_club__name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    context = {
        'title': _("Transfer Management"),
        'transfer_stats': transfer_stats,
        'pending_transfers': pending_transfers,
        'recent_transfers': recent_transfers,
        'monthly_transfers': monthly_transfers,
        'outgoing_transfers': outgoing,
        'incoming_transfers': incoming,
    }
    
    return render(request, 'admin/membership/transfer_management.html', context)


@staff_member_required
def workflow_monitoring(request):
    """Registration workflow monitoring dashboard"""
    
    # Workflow completion statistics
    workflows = RegistrationWorkflow.objects.all()
    
    completion_stats = {
        'completed': workflows.filter(completion_percentage=100).count(),
        'in_progress': workflows.filter(
            completion_percentage__gt=0,
            completion_percentage__lt=100
        ).count(),
        'not_started': workflows.filter(completion_percentage=0).count(),
        'blocked': workflows.filter(
            Q(personal_info_status='BLOCKED') |
            Q(club_selection_status='BLOCKED') |
            Q(document_upload_status='BLOCKED') |
            Q(payment_status='BLOCKED') |
            Q(club_approval_status='BLOCKED') |
            Q(safa_approval_status='BLOCKED')
        ).count(),
    }
    
    # Step completion breakdown
    step_stats = {
        'personal_info': workflows.filter(personal_info_status='COMPLETED').count(),
        'club_selection': workflows.filter(club_selection_status='COMPLETED').count(),
        'document_upload': workflows.filter(document_upload_status='COMPLETED').count(),
        'payment': workflows.filter(payment_status='COMPLETED').count(),
        'club_approval': workflows.filter(club_approval_status='COMPLETED').count(),
        'safa_approval': workflows.filter(safa_approval_status='COMPLETED').count(),
    }
    
    # Incomplete workflows requiring attention
    incomplete_workflows = workflows.filter(
        completion_percentage__lt=100
    ).order_by('completion_percentage', 'created')[:20]
    
    # Blocked workflows
    blocked_workflows = workflows.filter(
        Q(personal_info_status='BLOCKED') |
        Q(club_selection_status='BLOCKED') |
        Q(document_upload_status='BLOCKED') |
        Q(payment_status='BLOCKED') |
        Q(club_approval_status='BLOCKED') |
        Q(safa_approval_status='BLOCKED')
    )[:10]
    
    # Average completion time analysis
    completed_workflows = workflows.filter(completion_percentage=100)
    if completed_workflows.exists():
        # This would require more sophisticated tracking of step completion dates
        # For now, we'll estimate based on member creation and workflow update dates
        avg_completion_days = "5-7 days"  # Placeholder
    else:
        avg_completion_days = "No data"
    
    context = {
        'title': _("Registration Workflow Monitoring"),
        'completion_stats': completion_stats,
        'step_stats': step_stats,
        'incomplete_workflows': incomplete_workflows,
        'blocked_workflows': blocked_workflows,
        'avg_completion_days': avg_completion_days,
    }
    
    return render(request, 'admin/membership/workflow_monitoring.html', context)


@staff_member_required
@user_passes_test(is_safa_admin)
def system_health_check(request):
    """System health and data integrity dashboard"""
    
    # Data integrity checks
    integrity_issues = []
    
    # Members without current season
    members_no_season = Member.objects.filter(current_season__isnull=True).count()
    if members_no_season > 0:
        integrity_issues.append({
            'type': 'warning',
            'message': f'{members_no_season} members without current season assignment',
            'action': 'Assign to active season'
        })
    
    # Members without clubs
    members_no_club = Member.objects.filter(current_club__isnull=True).count()
    if members_no_club > 0:
        integrity_issues.append({
            'type': 'error',
            'message': f'{members_no_club} members without club assignment',
            'action': 'Members must select a club'
        })
    
    # Invoices without line items
    invoices_no_items = Invoice.objects.filter(items__isnull=True).count()
    if invoices_no_items > 0:
        integrity_issues.append({
            'type': 'error',
            'message': f'{invoices_no_items} invoices without line items',
            'action': 'Add invoice items or cancel invoices'
        })
    
    # Members without workflows
    members_no_workflow = Member.objects.filter(workflow__isnull=True).count()
    if members_no_workflow > 0:
        integrity_issues.append({
            'type': 'info',
            'message': f'{members_no_workflow} members without workflow tracking',
            'action': 'Workflow will be created automatically'
        })
    
    # System statistics
    system_stats = {
        'total_members': Member.objects.count(),
        'total_invoices': Invoice.objects.count(),
        'total_transfers': Transfer.objects.count(),
        'active_seasons': SAFASeasonConfig.objects.filter(is_active=True).count(),
        'database_size': 'N/A',  # Would require database-specific queries
        'last_backup': 'N/A',   # Would require backup system integration
    }
    
    # Performance metrics (simplified)
    performance_metrics = {
        'avg_response_time': 'N/A',
        'memory_usage': 'N/A',
        'database_connections': 'N/A',
        'cache_hit_rate': 'N/A',
    }
    
    context = {
        'title': _("System Health Check"),
        'integrity_issues': integrity_issues,
        'system_stats': system_stats,
        'performance_metrics': performance_metrics,
        'health_status': 'Good' if len(integrity_issues) == 0 else 'Issues Found',
    }
    
    return render(request, 'admin/membership/system_health.html', context)


# ============================================================================
# AJAX VIEWS FOR DYNAMIC CONTENT
# ============================================================================

@staff_member_required
def ajax_member_search(request):
    """AJAX endpoint for member search"""
    from django.http import JsonResponse
    
    query = request.GET.get('q', '').strip()
    if len(query) < 3:
        return JsonResponse({'results': []})
    
    members = Member.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(safa_id__icontains=query) |
        Q(email__icontains=query)
    )[:10]
    
    results = []
    for member in members:
        results.append({
            'id': member.id,
            'safa_id': member.safa_id,
            'name': member.get_full_name(),
            'email': member.email,
            'status': member.get_status_display(),
            'club': member.current_club.name if member.current_club else 'No Club',
        })
    
    return JsonResponse({'results': results})


@staff_member_required
def ajax_invoice_details(request, invoice_id):
    """AJAX endpoint for invoice details"""
    from django.http import JsonResponse
    from django.shortcuts import get_object_or_404
    
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    data = {
        'invoice_number': invoice.invoice_number,
        'total_amount': str(invoice.total_amount),
        'paid_amount': str(invoice.paid_amount),
        'status': invoice.get_status_display(),
        'due_date': invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else None,
        'billed_to': str(invoice.member) if invoice.member else str(invoice.organization),
        'items': []
    }
    
    for item in invoice.items.all():
        data['items'].append({
            'description': item.description,
            'quantity': item.quantity,
            'unit_price': str(item.unit_price),
            'sub_total': str(item.sub_total),
        })
    
    return JsonResponse(data)