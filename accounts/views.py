# accounts/views.py
from django.utils.crypto import get_random_string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.urls import reverse
from django.contrib import messages
from django.db import models, transaction
from django.contrib.auth.decorators import login_required

from .forms import EmailAuthenticationForm
from .models import CustomUser
from membership.models import Member

import logging
logger = logging.getLogger(__name__)

class ModernLoginView(LoginView):
    """Modern login view with enhanced security and UX"""
    form_class = EmailAuthenticationForm
    template_name = 'accounts/modern_login.html'
    redirect_authenticated_user = True

@login_required
def modern_home(request):
    """Modern home dashboard for authenticated users"""
    user = request.user
    try:
        member = user.member_profile
    except Member.DoesNotExist:
        member = None

    context = {
        'title': 'SAFA Dashboard',
        'user': user,
        'member': member,
    }
    
    return render(request, 'accounts/modern_home.html', context)






def get_system_status():
    """Get overall system status"""
    return {
        'operational': True,
        'last_updated': timezone.now(),
        'maintenance_scheduled': False
    }


def get_monthly_registration_count():
    """Get registration count for current month"""
    try:
        current_month = timezone.now().replace(day=1)
        return CustomUser.objects.filter(
            date_joined__gte=current_month
        ).count()
    except Exception:
        return 0


def get_monthly_revenue():
    """Get revenue for current month"""
    try:
        from membership.models import Invoice
        current_month = timezone.now().replace(day=1)
        return Invoice.objects.filter(
            status='PAID',
            paid_date__gte=current_month
        ).aggregate(total=models.Sum('amount'))['total'] or 0
    except Exception:
        return 0


def calculate_compliance_rate(members):
    """Calculate compliance rate for a set of members"""
    try:
        if not members.exists():
            return 0
        
        compliant_members = 0
        total_members = members.count()
        
        for member in members:
            if member.get_compliance_score() >= 80:  # 80% compliance threshold
                compliant_members += 1
        
        return int((compliant_members / total_members) * 100)
    except Exception:
        return 0


# Placeholder functions - implement based on your specific requirements





































def get_club_recent_registrations(club):
    """Get recent registrations for club"""
    if not club:
        return []
    
    try:
        return CustomUser.objects.filter(
            club=club,
            date_joined__gte=timezone.now() - timedelta(days=30)
        ).order_by('-date_joined')[:5]
    except Exception:
        return []














def get_recent_payments(limit=10):
    """Get recent payments"""
    try:
        from membership.models import Invoice
        return Invoice.objects.filter(
            status='PAID',
            paid_date__isnull=False
        ).order_by('-paid_date')[:limit]
    except Exception:
        return []


def get_pending_invoices_count():
    """Get count of pending invoices"""
    try:
        from membership.models import Invoice
        return Invoice.objects.filter(
            status__in=['PENDING', 'OVERDUE']
        ).count()
    except Exception:
        return 0


def get_revenue_summary():
    """Get revenue summary for current and previous periods"""
    try:
        from membership.models import Invoice
        from datetime import date
        
        # Current month
        current_month_start = timezone.now().replace(day=1)
        current_month_revenue = Invoice.objects.filter(
            status='PAID',
            paid_date__gte=current_month_start
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        # Previous month
        if current_month_start.month == 1:
            prev_month_start = current_month_start.replace(year=current_month_start.year - 1, month=12)
        else:
            prev_month_start = current_month_start.replace(month=current_month_start.month - 1)
        
        prev_month_end = current_month_start - timedelta(days=1)
        
        prev_month_revenue = Invoice.objects.filter(
            status='PAID',
            paid_date__gte=prev_month_start,
            paid_date__lte=prev_month_end
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        # Calculate growth
        growth = 0
        if prev_month_revenue > 0:
            growth = ((current_month_revenue - prev_month_revenue) / prev_month_revenue) * 100
        
        return {
            'current_month': current_month_revenue,
            'previous_month': prev_month_revenue,
            'growth_percentage': round(growth, 1)
        }
    
    except Exception as e:
        logger.error(f"Error getting revenue summary: {e}")
        return {
            'current_month': 0,
            'previous_month': 0,
            'growth_percentage': 0
        }


def log_user_activity(user, action, details=""):
    """Log user activity for audit trail"""
    try:
        # You can implement this with a UserActivity model
        # or use Django's built-in logging
        logger.info(f"User Activity - User: {user.email if user else 'Anonymous'}, Action: {action}, Details: {details}")
    except Exception as e:
        logger.error(f"Error logging user activity: {e}")


# AJAX Views for dynamic form updates

@require_GET
def get_regions_for_province(request):
    """AJAX view to get regions for selected province"""
    province_id = request.GET.get('province_id')
    
    if not province_id:
        return JsonResponse({'regions': []})
    
    try:
        regions = Region.objects.filter(province_id=province_id).values('id', 'name')
        return JsonResponse({'regions': list(regions)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_GET
def get_lfas_for_region(request):
    """AJAX view to get LFAs for selected region"""
    region_id = request.GET.get('region_id')
    
    if not region_id:
        return JsonResponse({'lfas': []})
    
    try:
        lfas = LocalFootballAssociation.objects.filter(region_id=region_id).values('id', 'name')
        return JsonResponse({'lfas': list(lfas)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_GET
def get_clubs_for_lfa(request):
    """AJAX view to get clubs for selected LFA"""
    lfa_id = request.GET.get('lfa_id')
    
    if not lfa_id:
        return JsonResponse({'clubs': []})
    
    try:
        clubs = Club.objects.filter(localfootballassociation_id=lfa_id).values('id', 'name')
        return JsonResponse({'clubs': list(clubs)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_GET
def dashboard_stats_api(request):
    """API endpoint for dashboard statistics"""
    user = request.user
    
    try:
        if user.role == 'ADMIN_NATIONAL':
            stats = get_national_admin_stats()
        elif user.role == 'ADMIN_NATIONAL_ACCOUNTS':
            stats = get_financial_stats()
        elif user.role in ['ADMIN_PROVINCE', 'ADMIN_REGION', 'ADMIN_LOCAL_FED']:
            stats = get_regional_admin_stats(user)
        elif user.role == 'CLUB_ADMIN':
            stats = get_club_stats(user.club)
        elif user.role == 'ASSOCIATION_ADMIN':
            stats = get_association_stats(user.association)
        else:
            stats = {}
        
        return JsonResponse({'stats': stats})
    
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return JsonResponse({'error': 'Unable to load statistics'}, status=500)


@login_required
@require_GET
def search_members_api(request):
    """API endpoint for member search autocomplete"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    try:
        # Get members based on user's permissions
        members = get_admin_jurisdiction_queryset(request.user).filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(safa_id__icontains=query)
        )[:10]
        
        results = []
        for member in members:
            results.append({
                'id': member.id,
                'name': member.get_full_name(),
                'email': member.email,
                'safa_id': member.safa_id or 'No SAFA ID',
                'role': member.get_role_display(),
                'status': member.membership_status,
                'avatar_url': member.profile_photo.url if member.profile_photo else None
            })
        
        return JsonResponse({'results': results})
    
    except Exception as e:
        logger.error(f"Error in member search API: {e}")
        return JsonResponse({'error': 'Search failed'}, status=500)


@login_required
@require_POST
def quick_approve_member(request):
    """Quick approve member via AJAX"""
    member_id = request.POST.get('member_id')
    
    if not member_id:
        return JsonResponse({'error': 'Member ID required'}, status=400)
    
    try:
        member = get_object_or_404(CustomUser, id=member_id)
        
        # Check permissions
        if not can_approve_member(request.user, member):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Check if member can be approved
        if not member.is_profile_complete:
            return JsonResponse({
                'error': 'Member profile is not complete',
                'details': 'Profile photo, ID document, and POPI consent required'
            }, status=400)
        
        # Approve member
        member.is_active = True
        member.membership_status = 'ACTIVE'
        member.membership_activated_date = timezone.now()
        
        if not member.safa_id:
            member.safa_id = generate_unique_safa_id()
        
        member.save()
        
        # Log the approval
        log_user_activity(
            user=request.user,
            action='approve_member',
            details=f"Approved member {member.get_full_name()} (ID: {member.id})"
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Member {member.get_full_name()} approved successfully',
            'member': {
                'id': member.id,
                'name': member.get_full_name(),
                'safa_id': member.safa_id,
                'status': member.membership_status
            }
        })
    
    except Exception as e:
        logger.error(f"Error in quick approve: {e}")
        return JsonResponse({'error': 'Approval failed'}, status=500)


# Error handling views

def custom_400_view(request, exception):
    """Custom 400 Bad Request page"""
    return render(request, 'errors/400.html', {
        'title': 'Bad Request',
        'message': 'The request could not be understood by the server.'
    }, status=400)


def custom_404_view(request, exception):
    """Custom 404 page"""
    return render(request, 'errors/404.html', {
        'title': 'Page Not Found',
        'message': 'The page you are looking for could not be found.',
        'show_search': True,
        'helpful_links': [
            {'title': 'Home', 'url': reverse('accounts:modern_home')},
            {'title': 'Registration Portal', 'url': reverse('accounts:registration_portal')},
            {'title': 'Help Center', 'url': reverse('accounts:help_center')},
        ]
    }, status=404)


def custom_500_view(request):
    """Custom 500 page"""
    return render(request, 'errors/500.html', {
        'title': 'Server Error',
        'message': 'An internal server error occurred. Please try again later.',
        'contact_email': 'support@safa.net',
        'show_report_form': True
    }, status=500)


def custom_403_view(request, exception):
    """Custom 403 page"""
    return render(request, 'errors/403.html', {
        'title': 'Access Denied',
        'message': 'You do not have permission to access this page.',
        'user_role': request.user.get_role_display() if request.user.is_authenticated else None,
        'contact_info': {
            'email': 'support@safa.net',
            'phone': '+27 11 494 3522'
        }
    }, status=403)



# Additional utility views

@login_required
def switch_organization(request):
    """Allow users with multiple roles to switch organization context"""
    if request.method == 'POST':
        org_type = request.POST.get('org_type')
        org_id = request.POST.get('org_id')
        
        # Store in session for context switching
        request.session['active_organization'] = {
            'type': org_type,
            'id': org_id
        }
        
        messages.success(request, 'Organization context switched successfully.')
        return redirect('accounts:modern_home')
    
    # Get user's available organizations
    organizations = get_user_organizations(request.user)
    
    context = {
        'title': 'Switch Organization',
        'organizations': organizations
    }
    
    return render(request, 'accounts/switch_organization.html', context)


def get_user_organizations(user):
    """Get list of organizations user belongs to"""
    organizations = []
    
    if user.national_federation:
        organizations.append({
            'type': 'national',
            'id': user.national_federation.id,
            'name': user.national_federation.name,
            'level': 'National'
        })
    
    if user.province:
        organizations.append({
            'type': 'province',
            'id': user.province.id,
            'name': user.province.name,
            'level': 'Province'
        })
    
    if user.region:
        organizations.append({
            'type': 'region',
            'id': user.region.id,
            'name': user.region.name,
            'level': 'Region'
        })
    
    if user.local_federation:
        organizations.append({
            'type': 'lfa',
            'id': user.local_federation.id,
            'name': user.local_federation.name,
            'level': 'LFA'
        })
    
    if user.club:
        organizations.append({
            'type': 'club',
            'id': user.club.id,
            'name': user.club.name,
            'level': 'Club'
        })
    
    if user.association:
        organizations.append({
            'type': 'association',
            'id': user.association.id,
            'name': user.association.name,
            'level': 'Association'
        })
    
    return organizations


@login_required
def notification_center(request):
    """Notification center for users"""
    notifications = get_all_user_notifications(request.user)
    
    context = {
        'title': 'Notifications',
        'notifications': notifications,
        'unread_count': len([n for n in notifications if not n.get('read', False)])
    }
    
    return render(request, 'accounts/notifications.html', context)


def get_all_user_notifications(user):
    """Get all notifications for user"""
    notifications = []
    
    # System notifications
    notifications.extend(get_user_notifications(user))
    
    # Add role-specific notifications
    if user.role in ['ADMIN_LOCAL_FED', 'ADMIN_REGION', 'ADMIN_PROVINCE', 'ADMIN_NATIONAL']:
        pending_count = get_admin_jurisdiction_queryset(user).filter(
            is_active=False,
            membership_status='PENDING'
        ).count()
        
        if pending_count > 0:
            notifications.append({
                'type': 'info',
                'title': 'Pending Approvals',
                'message': f'You have {pending_count} member(s) waiting for approval',
                'action_url': reverse('accounts:member_approvals'),
                'timestamp': timezone.now(),
                'read': False
            })
    
    notifications.sort(key=lambda x: x.get('timestamp', timezone.now()), reverse=True)
    
    return notifications





@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    # Implement notification read tracking
    # This would typically update a UserNotification model
    return JsonResponse({'success': True})


@require_GET
def health_check(request):
    """Health check endpoint for monitoring"""
    try:
        # Check database connectivity
        user_count = CustomUser.objects.count()
        
        # Check critical services
        status = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'database': 'connected',
            'user_count': user_count,
            'services': {
                'authentication': 'operational',
                'payments': 'operational'
            }
        }
        
        return JsonResponse(status)
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=503)


# Import required helper functions that should already exist
# If these don't exist, you'll need to implement them based on your system

def get_dashboard_stats():
    """Get general dashboard statistics"""
    return {
        'total_users': CustomUser.objects.count(),
        'active_users': CustomUser.objects.filter(is_active=True).count(),
        'registrations_today': CustomUser.objects.filter(
            date_joined__date=timezone.now().date()
        ).count()
    }

def custom_404_view(request, exception):
    """Custom 404 page"""
    return render(request, 'errors/404.html', {
        'title': 'Page Not Found',
        'message': 'The page you are looking for could not be found.'
    }, status=404)


def custom_500_view(request):
    """Custom 500 page"""
    return render(request, 'errors/500.html', {
        'title': 'Server Error',
        'message': 'An internal server error occurred. Please try again later.'
    }, status=500)


def custom_403_view(request, exception):
    """Custom 403 page"""
    return render(request, 'errors/403.html', {
        'title': 'Access Denied',
        'message': 'You do not have permission to access this page.'
    }, status=403)




# Additional registration views for specific types













# AJAX views for dynamic form updates during registration

def get_organization_types_api(request):
    """API to get organization types based on selected level"""
    level = request.GET.get('level')
    
    if not level:
        return JsonResponse({'organization_types': []})
    
    try:
        org_types = OrganizationType.objects.filter(
            level=level,
            is_active=True
        ).values('id', 'name')
        
        return JsonResponse({'organization_types': list(org_types)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def get_positions_for_org_type_api(request):
    """API to get positions available for organization type"""
    org_type_id = request.GET.get('org_type_id')
    
    if not org_type_id:
        return JsonResponse({'positions': []})
    
    try:
        org_type = OrganizationType.objects.get(id=org_type_id)
        
        # Get positions that can be used at this level
        positions = Position.objects.filter(
            is_active=True,
            levels__icontains=org_type.level
        ).values('id', 'title', 'description')
        
        return JsonResponse({'positions': list(positions)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)











# Helper function to create user invoice (implement based on your invoice system)
def create_member_invoice(user):
    """Create invoice for member registration"""
    try:
        # This should integrate with your existing invoice system
        from membership.models import Invoice
        
        # Determine fee based on user role
        fee_amount = get_registration_fee(user.role)
        
        if fee_amount > 0:
            invoice = Invoice.objects.create(
                user=user,
                invoice_type='REGISTRATION',
                description=f'SAFA Registration Fee - {user.get_role_display()}',
                amount=fee_amount,
                due_date=timezone.now().date() + timezone.timedelta(days=30),
                status='PENDING'
            )
            return invoice
    
    except Exception as e:
        logger.error(f"Error creating invoice: {e}")
        raise


def get_registration_fee(role):
    """Get registration fee based on role"""
    fees = {
        'PLAYER': 150.00,
        'OFFICIAL': 200.00,
        'CLUB_ADMIN': 300.00,
        'ASSOCIATION_ADMIN': 500.00,
        'ADMIN_LOCAL_FED': 0.00,  # No fee for LFA admins
        'ADMIN_REGION': 0.00,
        'ADMIN_PROVINCE': 0.00,
        'ADMIN_NATIONAL': 0.00,
        'ADMIN_NATIONAL_ACCOUNTS': 0.00
    }
    return fees.get(role, 150.00)  # Default fee


@login_required
def club_admin_add_player(request):
    if request.user.role != 'CLUB_ADMIN':
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('accounts:home')

    if request.method == 'POST':
        form = PlayerForm(request.POST)
        if form.is_valid():
            player = form.save(commit=False)
            player.role = 'PLAYER'
            player.club = request.user.club
            # Set a random password for the new player
            password = get_random_string(12)
            player.set_password(password)
            player.save()

            # Create an invoice for the new player
            try:
                invoice = create_member_invoice(player)
                if invoice:
                    messages.success(request, f"Player {player.get_full_name()} added successfully. Invoice #{invoice.invoice_number} has been created.")
                else:
                    messages.success(request, f"Player {player.get_full_name()} added successfully. No invoice was required.")
            except Exception as e:
                messages.warning(request, f"Player {player.get_full_name()} added, but failed to create an invoice. Error: {e}")

            return redirect('accounts:home')
    else:
        form = PlayerForm()

    context = {
        'form': form,
        'title': 'Add New Player'
    }
    return render(request, 'accounts/club_admin_add_player.html', context)
