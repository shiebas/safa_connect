from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from django.contrib.sessions.models import Session
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from membership.models import Invoice
from membership.models import Member
from geography.models import Club
from accounts.models import CustomUser
from accounts.forms import UserManagementForm


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
    pending_approvals = Member.objects.filter(status='PENDING').select_related('user', 'current_club')

    # All Members list
    all_members_list = CustomUser.objects.all().order_by('first_name', 'last_name')
    member_paginator = Paginator(all_members_list, 10)
    member_page_number = request.GET.get('member_page', 1)
    members_page = member_paginator.get_page(member_page_number)

    # ==== USER MANAGEMENT ====
    # Get all users with pagination
    users_list = CustomUser.objects.all().order_by('-date_joined')
    user_paginator = Paginator(users_list, 15)
    user_page_number = request.GET.get('user_page', 1)
    users_page = user_paginator.get_page(user_page_number)

    context = {
        'online_users': online_users,
        'invoice_metrics': invoice_metrics,
        'membership_metrics': membership_metrics,
        'invoice_by_type': invoice_by_type,
        'recent_activities': recent_activities,
        'pending_approvals': pending_approvals,
        'members_page': members_page,
        'users_page': users_page,
    }
    
    return render(request, 'admin/superuser_dashboard.html', context)


@staff_member_required
def user_management(request):
    """User management interface for superusers"""
    if not request.user.is_superuser:
        messages.error(request, 'Only superusers can access user management.')
        return redirect('superuser_dashboard')
    
    # Get all users with pagination and search
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    
    users = CustomUser.objects.all()
    
    # Apply search filter
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query)
        )
    
    # Apply role filter
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Apply status filter
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(users.order_by('-date_joined'), 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get unique roles for filter dropdown
    roles = CustomUser.objects.values_list('role', flat=True).distinct().exclude(role__isnull=True)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'roles': roles,
        'total_users': users.count(),
    }
    
    return render(request, 'admin/user_management.html', context)


@staff_member_required
def edit_user(request, user_id):
    """Edit user details"""
    if not request.user.is_superuser:
        messages.error(request, 'Only superusers can edit users.')
        return redirect('user_management')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        form = UserManagementForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {user.get_full_name()} updated successfully.')
            return redirect('user_management')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserManagementForm(instance=user)
    
    context = {
        'form': form,
        'user': user,
        'title': f'Edit User: {user.get_full_name()}'
    }
    
    return render(request, 'admin/edit_user.html', context)


@staff_member_required
def delete_user(request, user_id):
    """Delete user (AJAX endpoint)"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Only superusers can delete users.'}, status=403)
    
    if request.method == 'POST':
        try:
            user = get_object_or_404(CustomUser, id=user_id)
            
            # Prevent self-deletion
            if user == request.user:
                return JsonResponse({'success': False, 'error': 'You cannot delete your own account.'}, status=400)
            
            user_name = user.get_full_name()
            user.delete()
            
            return JsonResponse({
                'success': True, 
                'message': f'User {user_name} deleted successfully.'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)


@staff_member_required
def toggle_user_status(request, user_id):
    """Toggle user active/inactive status (AJAX endpoint)"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Only superusers can modify user status.'}, status=403)
    
    if request.method == 'POST':
        try:
            user = get_object_or_404(CustomUser, id=user_id)
            
            # Prevent self-deactivation
            if user == request.user:
                return JsonResponse({'success': False, 'error': 'You cannot deactivate your own account.'}, status=400)
            
            user.is_active = not user.is_active
            user.save()
            
            status = 'activated' if user.is_active else 'deactivated'
            return JsonResponse({
                'success': True, 
                'message': f'User {user.get_full_name()} {status} successfully.',
                'is_active': user.is_active
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)
