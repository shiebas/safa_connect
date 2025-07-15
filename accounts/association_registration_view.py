from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms
from .forms import UniversalRegistrationForm
from geography.models import Association

def association_registration(request):
    """Registration view for association admins (referee associations)"""
    
    if request.method == 'POST':
        print("[DEBUG - REFEREE REG] Received POST request for association registration")
        print(f"[DEBUG - REFEREE REG] POST data: {request.POST}")
        print(f"[DEBUG - REFEREE REG] FILES data: {request.FILES}")
        
        form = UniversalRegistrationForm(request.POST, request.FILES, request=request)
        # Set the role to ASSOCIATION_ADMIN
        if form.is_valid():
            print("[DEBUG - REFEREE REG] Form is valid, proceeding with user creation")
            user = form.save(commit=False)
            user.role = 'ASSOCIATION_ADMIN'
            
            # Get the association from the form
            association = form.cleaned_data.get('association')
            if association:
                user.association = association
                print(f"[DEBUG - REFEREE REG] Set user association to: {association}")
                
                # Always set the national federation to SAFA
                try:
                    from geography.models import NationalFederation
                    safa_federation = NationalFederation.objects.filter(
                        name__icontains="South African Football").first()
                    if safa_federation:
                        user.national_federation = safa_federation
                        print(f"[DEBUG - REFEREE REG] Set user national federation to: {safa_federation}")
                    else:
                        print("[DEBUG - REFEREE REG] Could not find SAFA national federation")
                except Exception as e:
                    print(f"[DEBUG - REFEREE REG] Error setting national federation: {e}")
                
                # Set the province, region and LFA based on the association
                if hasattr(association, 'province') and association.province:
                    user.province = association.province
                if hasattr(association, 'region') and association.region:
                    user.region = association.region
                if hasattr(association, 'local_football_association') and association.local_football_association:
                    user.local_federation = association.local_football_association
            
            user.save()
            messages.success(request, 'Association administrator account created successfully! Your account is pending approval.')
            return redirect('accounts:login')
        else:
            print("[DEBUG - REFEREE REG] Form is invalid")
            print(form.errors)
            return render(request, 'accounts/association_registration.html', {
                'form': form,
                'title': 'Referee Association Administrator Registration'
            })

    else:
        form = UniversalRegistrationForm(request=request)
        # Modify the form to show association field
        if hasattr(form.fields, 'association'):
            form.fields['association'].required = True
            
            # Get all associations that might be referee associations
            referee_associations = Association.objects.filter(
                name__icontains='referee'
            ) | Association.objects.filter(
                type__icontains='referee'
            )
            
            # If we didn't find any, show all associations as a fallback
            if not referee_associations.exists():
                referee_associations = Association.objects.all()
                
            form.fields['association'].queryset = referee_associations
            print(f"[DEBUG - REFEREE REG] Available referee associations: {[a.name for a in referee_associations]}")
        
        # Set role field to ASSOCIATION_ADMIN and make it a hidden input
        if 'role' in form.fields:
            form.fields['role'].initial = 'ASSOCIATION_ADMIN'
            form.fields['role'].widget = forms.HiddenInput()
            # Add a hidden field to the form to ensure the role is submitted
            print("[DEBUG - REFEREE REG] Setting role field to hidden with value ASSOCIATION_ADMIN")
            
        # Set organization_type and hide the field
        if 'organization_type' in form.fields:
            # Since we can't import OrganizationType reliably, we'll handle it differently
            
            # Set the field to not required and hide it
            form.fields['organization_type'].required = False
            form.fields['organization_type'].widget = forms.HiddenInput()
            
            # Try to set a default value if possible (using direct DB query)
            try:
                from .models import OrganizationType
                
                # First try to find an organization type specifically for associations
                association_type = OrganizationType.objects.filter(
                    level='ASSOCIATION'
                ).filter(
                    name__icontains='referee'
                ).first()
                
                # If not found, get any ASSOCIATION level type
                if not association_type:
                    association_type = OrganizationType.objects.filter(
                        level='ASSOCIATION'
                    ).first()
                
                # If still not found, create one
                if not association_type:
                    association_type = OrganizationType.objects.create(
                        name="Referee Association",
                        level="ASSOCIATION",
                        requires_approval=True,
                        is_active=True
                    )
                    print(f"[DEBUG - REFEREE REG] Created new organization type: {association_type}")
                
                form.fields['organization_type'].initial = association_type.id
                print(f"[DEBUG - REFEREE REG] Set organization type to: {association_type}")
                
            except Exception as e:
                print(f"[DEBUG - REFEREE REG] Error setting organization type: {e}")
                # If that fails, try using direct DB query as fallback
                try:
                    from django.db import connection
                    with connection.cursor() as cursor:
                        # First try to find organization type with ASSOCIATION level
                        cursor.execute(
                            "SELECT id FROM accounts_organizationtype WHERE level = 'ASSOCIATION' LIMIT 1"
                        )
                        result = cursor.fetchone()
                        
                        # If not found, try finding any referee-related organization type
                        if not result:
                            cursor.execute(
                                "SELECT id FROM accounts_organizationtype WHERE name ILIKE %s LIMIT 1", 
                                ['%referee%']
                            )
                            result = cursor.fetchone()
                        
                        if result and result[0]:
                            form.fields['organization_type'].initial = result[0]
                            print(f"[DEBUG - REFEREE REG] Set organization type via DB query to: {result[0]}")
                except Exception as e2:
                    print(f"[DEBUG - REFEREE REG] Database query for organization type failed: {e2}")
                
        # Hide all club-related fields since they're not relevant for referee association admins
        for field_name in ['club', 'local_federation']:
            if field_name in form.fields:
                form.fields[field_name].required = False
                form.fields[field_name].widget = forms.HiddenInput()
                form.fields[field_name].initial = None
                print(f"[DEBUG - REFEREE REG] Hidden {field_name} field for referee admin registration")
                
    
    return render(request, 'accounts/association_registration.html', {
        'form': form,
        'title': 'Referee Association Administrator Registration'
    })