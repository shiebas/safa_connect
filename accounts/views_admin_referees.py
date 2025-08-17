from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .forms import AssociationOfficialRegistrationForm
from .models import CustomUser, Position
from geography.models import Association, LocalFootballAssociation, Region, Province

@login_required
def admin_add_referee(request):
    """
    Universal view for all admin levels (Provincial, Regional, LFA, Association)
    to register referees.
    """
    # Check if user has appropriate role (including superusers)
    allowed_roles = ['ADMIN_PROVINCE', 'ADMIN_REGION', 'ADMIN_LOCAL_FED', 'ASSOCIATION_ADMIN']
    if not (request.user.is_superuser or request.user.is_staff or 
            (hasattr(request.user, 'role') and request.user.role in allowed_roles)):
        messages.error(request, "You don't have permission to register referees.")
        return redirect('accounts:home')
    
    if request.method == 'POST':
        official_form = AssociationOfficialRegistrationForm(request.POST, request.FILES)
        
        if official_form.is_valid():
            user = official_form.save(commit=False)
            user.role = 'OFFICIAL'
            user.position = referee_position
            user.created_by = request.user
            user.save()
            
            # Handle association assignment based on admin role
            if request.user.role == 'ASSOCIATION_ADMIN':
                # For association admins, use their association
                if hasattr(request.user, 'association') and request.user.association:
                    user.association = request.user.association
            elif request.user.role == 'ADMIN_LOCAL_FED':
                # For LFA admins, create association link if needed
                lfa = request.user.local_federation
                if lfa:
                    # Get or create national federation
                    from geography.models import NationalFederation
                    national_federation = NationalFederation.objects.first()  # Assuming one national federation
                    
                    if national_federation:
                        lfa_association, created = Association.objects.get_or_create(
                            name=f"{lfa.name} Referees Association",
                            defaults={
                                'national_federation': national_federation,
                                'description': 'Referee association for ' + lfa.name
                            }
                        )
                        user.association = lfa_association
            elif request.user.role == 'ADMIN_REGION':
                # For Regional admins, create regional association link
                region = request.user.region
                if region:
                    # Get or create national federation
                    from geography.models import NationalFederation
                    national_federation = NationalFederation.objects.first()  # Assuming one national federation
                    
                    if national_federation:
                        region_association, created = Association.objects.get_or_create(
                            name=f"{region.name} Referees Association",
                            defaults={
                                'national_federation': national_federation,
                                'description': 'Referee association for ' + region.name
                            }
                        )
                        user.association = region_association
            elif request.user.role == 'ADMIN_PROVINCE':
                # For Provincial admins, create provincial association link
                province = request.user.province
                if province:
                    # Get or create national federation
                    from geography.models import NationalFederation
                    national_federation = NationalFederation.objects.first()  # Assuming one national federation
                    
                    if national_federation:
                        province_association, created = Association.objects.get_or_create(
                            name=f"{province.name} Referees Association",
                            defaults={
                                'national_federation': national_federation,
                                'description': 'Referee association for ' + province.name
                            }
                        )
                        user.association = province_association
            
            messages.success(request, 'Referee registration successful!')
            user.save()
            return redirect('accounts:official_list')
        else:
            messages.error(request, 'Please correct the errors in the form below.')
    else:
        official_form = AssociationOfficialRegistrationForm()
    
    return render(request, 'accounts/admin_add_referee.html', {
        'official_form': official_form
    })
