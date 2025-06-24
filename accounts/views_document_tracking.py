"""
Document access tracking views for SAFA Global system
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
from accounts.models import DocumentAccessLog


@login_required
@staff_member_required
def document_access_dashboard(request):
    """Dashboard showing document access statistics"""
    
    # Get date range filter
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Filter logs based on user role
    logs = DocumentAccessLog.objects.filter(access_time__gte=start_date)
    
    # Apply role-based filtering
    if not request.user.is_superuser:
        if request.user.role == 'CLUB_ADMIN' and request.user.club:
            logs = logs.filter(user__club=request.user.club)
        elif request.user.role == 'ADMIN_LOCAL_FED' and request.user.local_federation:
            logs = logs.filter(user__local_federation=request.user.local_federation)
        elif request.user.role == 'ADMIN_REGION' and request.user.region:
            logs = logs.filter(user__region=request.user.region)
        elif request.user.role == 'ADMIN_PROVINCE' and request.user.province:
            logs = logs.filter(user__province=request.user.province)
        elif request.user.role != 'ADMIN_COUNTRY':
            logs = logs.none()
    
    # Calculate statistics
    total_downloads = logs.filter(action='download').count()
    total_views = logs.filter(action='view').count()
    watermarked_downloads = logs.filter(action='download', watermarked=True).count()
    failed_attempts = logs.filter(success=False).count()
    
    # Top downloaders
    top_downloaders = logs.filter(action='download').values(
        'user__first_name', 'user__last_name', 'user__email', 'user__role'
    ).annotate(
        download_count=Count('id')
    ).order_by('-download_count')[:10]
    
    # Document type breakdown
    doc_type_stats = logs.filter(action='download').values(
        'document_type'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Daily download trends (last 7 days)
    daily_stats = []
    for i in range(7):
        date = timezone.now().date() - timedelta(days=i)
        count = logs.filter(
            action='download',
            access_time__date=date
        ).count()
        daily_stats.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    daily_stats.reverse()
    
    # Recent suspicious activity
    suspicious_activity = logs.filter(
        Q(success=False) | Q(notes__icontains='unauthorized')
    ).order_by('-access_time')[:20]
    
    context = {
        'total_downloads': total_downloads,
        'total_views': total_views,
        'watermarked_downloads': watermarked_downloads,
        'failed_attempts': failed_attempts,
        'watermark_percentage': round((watermarked_downloads / total_downloads * 100) if total_downloads > 0 else 0, 1),
        'top_downloaders': top_downloaders,
        'doc_type_stats': doc_type_stats,
        'daily_stats': daily_stats,
        'suspicious_activity': suspicious_activity,
        'days': days,
        'start_date': start_date,
    }
    
    return render(request, 'accounts/document_access_dashboard.html', context)


@login_required
@staff_member_required
def document_access_api(request):
    """API endpoint for document access data"""
    
    # Get parameters
    days = int(request.GET.get('days', 30))
    action = request.GET.get('action', 'download')
    
    start_date = timezone.now() - timedelta(days=days)
    
    # Filter logs
    logs = DocumentAccessLog.objects.filter(
        access_time__gte=start_date,
        action=action
    )
    
    # Apply role-based filtering
    if not request.user.is_superuser:
        if request.user.role == 'CLUB_ADMIN' and request.user.club:
            logs = logs.filter(user__club=request.user.club)
        elif request.user.role == 'ADMIN_LOCAL_FED' and request.user.local_federation:
            logs = logs.filter(user__local_federation=request.user.local_federation)
        elif request.user.role == 'ADMIN_REGION' and request.user.region:
            logs = logs.filter(user__region=request.user.region)
        elif request.user.role == 'ADMIN_PROVINCE' and request.user.province:
            logs = logs.filter(user__province=request.user.province)
        elif request.user.role != 'ADMIN_COUNTRY':
            logs = logs.none()
    
    # Get daily counts
    daily_data = []
    for i in range(days):
        date = timezone.now().date() - timedelta(days=i)
        count = logs.filter(access_time__date=date).count()
        daily_data.append({
            'date': date.isoformat(),
            'count': count
        })
    
    daily_data.reverse()
    
    return JsonResponse({
        'daily_data': daily_data,
        'total_count': logs.count()
    })


@login_required
def document_access_report(request):
    """Generate document access report for user's role"""
    
    # Get date range
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Filter logs for user's scope
    logs = DocumentAccessLog.objects.filter(access_time__gte=start_date)
    
    # Apply role-based filtering
    if not request.user.is_superuser:
        if request.user.role == 'CLUB_ADMIN' and request.user.club:
            logs = logs.filter(user__club=request.user.club)
            scope = f"Club: {request.user.club.name}"
        elif request.user.role == 'ADMIN_LOCAL_FED' and request.user.local_federation:
            logs = logs.filter(user__local_federation=request.user.local_federation)
            scope = f"LFA: {request.user.local_federation.name}"
        elif request.user.role == 'ADMIN_REGION' and request.user.region:
            logs = logs.filter(user__region=request.user.region)
            scope = f"Region: {request.user.region.name}"
        elif request.user.role == 'ADMIN_PROVINCE' and request.user.province:
            logs = logs.filter(user__province=request.user.province)
            scope = f"Province: {request.user.province.name}"
        elif request.user.role == 'ADMIN_COUNTRY':
            scope = "National"
        else:
            logs = logs.none()
            scope = "No access"
    else:
        scope = "System-wide (Superuser)"
    
    # Generate report data
    report_data = {
        'scope': scope,
        'period': f"Last {days} days",
        'total_logs': logs.count(),
        'downloads': logs.filter(action='download').count(),
        'views': logs.filter(action='view').count(),
        'failed_attempts': logs.filter(success=False).count(),
        'watermarked': logs.filter(watermarked=True).count(),
        'user_count': logs.values('user').distinct().count(),
        'document_types': list(logs.values('document_type').annotate(
            count=Count('id')
        ).order_by('-count')),
        'recent_activity': logs.order_by('-access_time')[:50]
    }
    
    return render(request, 'accounts/document_access_report.html', {
        'report_data': report_data,
        'days': days
    })
