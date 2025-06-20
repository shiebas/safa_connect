def association_registration(request):
    """Registration view for association admins (referee associations)"""
    if request.method == 'POST':
        form = UniversalRegistrationForm(request.POST, request.FILES)
        # Set the role to ASSOCIATION_ADMIN
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'ASSOCIATION_ADMIN'
            
            # Get the association from the form
            association = form.cleaned_data.get('association')
            if association:
                user.association = association
                
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
        form = UniversalRegistrationForm()
        # Modify the form to show association field
        if hasattr(form.fields, 'association'):
            form.fields['association'].required = True
            # Filter associations that are for referees
            from geography.models import Association
            form.fields['association'].queryset = Association.objects.filter(
                type__icontains='referee'
            )
        
        # Set role field to ASSOCIATION_ADMIN and make it read-only
        if 'role' in form.fields:
            form.fields['role'].initial = 'ASSOCIATION_ADMIN'
            form.fields['role'].widget.attrs['readonly'] = True
    
    return render(request, 'accounts/association_registration.html', {
        'form': form,
        'title': 'Referee Association Administrator Registration'
    })
