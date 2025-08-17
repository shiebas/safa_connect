"""
Document Access Dashboard Views
Provides analytics and monitoring for document downloads
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, Http404
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib import messages
import csv
import io
from datetime import timedelta
from .models import DocumentAccessLog, CustomUser
from .document_middleware import track_document_access
import logging

logger = logging.getLogger(__name__)

@login_required
def document_access_dashboard(request):
    """Main dashboard for document access analytics"""
    
    # Check permissions - only superusers and high-level admins can view this
    allowed_roles = ['ADMIN_SYSTEM', 'ADMIN_COUNTRY', 'ADMIN_FEDERATION', 'ADMIN_PROVINCE', 'ADMIN_REGION', 'ADMIN_LOCAL_FED']
    if not (request.user.is_superuser or request.user.role in allowed_roles):
        messages.error(request, 'You do not have permission to access this dashboard.')
        return redirect('accounts:home')
    
    # Get date range from query params
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Base queryset for the date range
    base_logs = DocumentAccessLog.objects.filter(access_time__gte=start_date)
    
    # Filter by user's scope if not superuser or national admin
    if not (request.user.is_superuser or request.user.role in ['ADMIN_SYSTEM', 'ADMIN_COUNTRY', 'ADMIN_FEDERATION']):
        if request.user.role == 'ADMIN_PROVINCE' and request.user.province:
            # Filter to users in the same province
            province_users = CustomUser.objects.filter(province=request.user.province)
            base_logs = base_logs.filter(user__in=province_users)
        elif request.user.role == 'ADMIN_REGION' and request.user.region:
            # Filter to users in the same region
            region_users = CustomUser.objects.filter(region=request.user.region)
            base_logs = base_logs.filter(user__in=region_users)
        elif request.user.role == 'ADMIN_LOCAL_FED' and request.user.local_federation:
            # Filter to users in the same LFA
            lfa_users = CustomUser.objects.filter(local_federation=request.user.local_federation)
            base_logs = base_logs.filter(user__in=lfa_users)
    
    # Calculate statistics
    total_downloads = base_logs.filter(action='download').count()
    total_views = base_logs.filter(action='view').count()
    watermarked_downloads = base_logs.filter(action='download', watermarked=True).count()
    failed_attempts = base_logs.filter(success=False).count()
    
    # Calculate watermark percentage
    watermark_percentage = 0
    if total_downloads > 0:
        watermark_percentage = round((watermarked_downloads / total_downloads) * 100, 1)
    
    # Daily statistics for chart
    daily_stats = []
    for i in range(days):
        day = start_date + timedelta(days=i)
        day_end = day + timedelta(days=1)
        count = base_logs.filter(
            access_time__gte=day,
            access_time__lt=day_end,
            action='download'
        ).count()
        daily_stats.append({
            'date': day.strftime('%m/%d'),
            'count': count
        })
    
    # Document type statistics
    doc_type_stats = base_logs.filter(action='download').values('document_type').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Top downloaders
    top_downloaders = base_logs.filter(action='download').values(
        'user__first_name', 'user__last_name', 'user__email', 'user__role'
    ).annotate(
        download_count=Count('id')
    ).order_by('-download_count')[:10]
    
    # Suspicious activity (failed attempts + high download volume)
    suspicious_activity = base_logs.filter(
        Q(success=False) | 
        Q(user__in=base_logs.filter(action='download').values('user').annotate(
            count=Count('id')
        ).filter(count__gte=10).values('user'))
    ).select_related('user').order_by('-access_time')[:20]
    
    context = {
        'days': days,
        'total_downloads': total_downloads,
        'total_views': total_views,
        'watermarked_downloads': watermarked_downloads,
        'failed_attempts': failed_attempts,
        'watermark_percentage': watermark_percentage,
        'daily_stats': daily_stats,
        'doc_type_stats': doc_type_stats,
        'top_downloaders': top_downloaders,
        'suspicious_activity': suspicious_activity,
    }
    
    return render(request, 'accounts/document_access_dashboard.html', context)

@login_required
def document_access_report(request):
    """Export document access report as CSV"""
    
    # Check permissions - only superusers and high-level admins can export
    allowed_roles = ['ADMIN_SYSTEM', 'ADMIN_COUNTRY', 'ADMIN_FEDERATION', 'ADMIN_PROVINCE', 'ADMIN_REGION', 'ADMIN_LOCAL_FED']
    if not (request.user.is_superuser or request.user.role in allowed_roles):
        raise Http404("Not authorized")
    
    # Get parameters
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Get data
    logs = DocumentAccessLog.objects.filter(
        access_time__gte=start_date
    ).select_related('user').order_by('-access_time')
    
    # Filter by scope if needed
    if not (request.user.is_superuser or request.user.role in ['ADMIN_SYSTEM', 'ADMIN_COUNTRY', 'ADMIN_FEDERATION']):
        if request.user.role == 'ADMIN_PROVINCE' and request.user.province:
            province_users = CustomUser.objects.filter(province=request.user.province)
            logs = logs.filter(user__in=province_users)
        elif request.user.role == 'ADMIN_REGION' and request.user.region:
            region_users = CustomUser.objects.filter(region=request.user.region)
            logs = logs.filter(user__in=region_users)
        elif request.user.role == 'ADMIN_LOCAL_FED' and request.user.local_federation:
            lfa_users = CustomUser.objects.filter(local_federation=request.user.local_federation)
            logs = logs.filter(user__in=lfa_users)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="safa_document_access_report_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Timestamp', 'User Name', 'User Email', 'User Role', 'Document Name', 
        'Document Type', 'Action', 'Watermarked', 'Success', 'IP Address', 'File Size'
    ])
    
    for log in logs:
        writer.writerow([
            log.access_time.strftime('%Y-%m-%d %H:%M:%S'),
            log.user.get_full_name(),
            log.user.email,
            log.user.role,
            log.document_name,
            log.document_type,
            log.action,
            'Yes' if log.watermarked else 'No',
            'Success' if log.success else 'Failed',
            log.ip_address,
            log.formatted_file_size
        ])
    
    return response

@login_required
def document_access_api(request):
    """API endpoint for real-time dashboard updates"""
    
    # Check permissions
    allowed_roles = ['ADMIN_SYSTEM', 'ADMIN_COUNTRY', 'ADMIN_FEDERATION', 'ADMIN_PROVINCE', 'ADMIN_REGION', 'ADMIN_LOCAL_FED']
    if not (request.user.is_superuser or request.user.role in allowed_roles):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Get recent activity (last hour)
    one_hour_ago = timezone.now() - timedelta(hours=1)
    recent_logs = DocumentAccessLog.objects.filter(
        access_time__gte=one_hour_ago
    ).select_related('user')
    
    # Filter by scope
    if not (request.user.is_superuser or request.user.role in ['ADMIN_SYSTEM', 'ADMIN_COUNTRY', 'ADMIN_FEDERATION']):
        if request.user.role == 'ADMIN_PROVINCE' and request.user.province:
            province_users = CustomUser.objects.filter(province=request.user.province)
            recent_logs = recent_logs.filter(user__in=province_users)
        elif request.user.role == 'ADMIN_REGION' and request.user.region:
            region_users = CustomUser.objects.filter(region=request.user.region)
            recent_logs = recent_logs.filter(user__in=region_users)
        elif request.user.role == 'ADMIN_LOCAL_FED' and request.user.local_federation:
            lfa_users = CustomUser.objects.filter(local_federation=request.user.local_federation)
            recent_logs = recent_logs.filter(user__in=lfa_users)
    
    data = {
        'recent_downloads': recent_logs.filter(action='download').count(),
        'recent_views': recent_logs.filter(action='view').count(),
        'recent_failures': recent_logs.filter(success=False).count(),
        'recent_activity': [
            {
                'user': log.user.get_full_name(),
                'document': log.document_name,
                'action': log.action,
                'time': log.access_time.strftime('%H:%M'),
                'watermarked': log.watermarked,
                'success': log.success
            }
            for log in recent_logs.order_by('-access_time')[:10]
        ]
    }
    
    return JsonResponse(data)

def protected_document_view(request, document_id):
    """Serve documents with protection and tracking"""
    
    if not request.user.is_authenticated:
        raise Http404("Document not found")
    
    # This would be customized based on your document storage system
    # For now, this is a placeholder that shows the concept
    
    try:
        # Track the access
        track_document_access(request.user, f"document_{document_id}", 'view')
        
        # Your document serving logic here
        # This could integrate with your existing media serving
        
        return HttpResponse("Document access tracked")
        
    except Exception as e:
        logger.error(f"Protected document access failed: {str(e)}")
        raise Http404("Document not available")
