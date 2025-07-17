from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import gettext_lazy as _
from .models import Member, Official, Transfer, MembershipApplication
from .invoice_models import Invoice

@staff_member_required
def national_admin_dashboard(request):
    """Dashboard view for National Admins"""

    # Filter for pending applications based on user role.
    # Superusers see all, others see based on their role.
    user = request.user
    if user.is_superuser or getattr(user, 'role', None) == 'ADMIN_NATIONAL':
        pending_applications = MembershipApplication.objects.filter(status='PENDING')
    else:
        # If other roles should see this dashboard, their logic would go here.
        # For now, we assume this dashboard is for National Admin level.
        pending_applications = MembershipApplication.objects.none()

    context = {
        'title': _("National Admin Dashboard"),
        'pending_members': Member.objects.filter(status='PENDING').count(),
        'pending_officials': Official.objects.filter(is_approved=False, status='PENDING').count(),
        'pending_transfers': Transfer.objects.filter(status='PENDING').count(),
        'pending_applications': pending_applications.count(),
        'overdue_invoices': Invoice.objects.filter(status='OVERDUE').count(),
    }
    return render(request, 'admin/membership/national_dashboard.html', context)
