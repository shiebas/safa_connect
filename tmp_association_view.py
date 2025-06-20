def association_admin_add_official(request):
    """View for an association admin to add a new official (particularly referees)"""
    # Check if user is authenticated and has the correct role
    if not request.user.is_authenticated or request.user.role != 'ASSOCIATION_ADMIN':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('accounts:dashboard')

    # Check if user is linked to an association
    if not hasattr(request.user, 'association') or not request.user.association:
        messages.error(request, 'Your user profile is not linked to an association. Please contact support.')
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        official_form = AssociationOfficialRegistrationForm(request.POST, request.FILES)
        # Store request in form to allow showing document validation warnings
        official_form.request = request
        # Process ID number before validation if provided
        if 'id_number' in request.POST and request.POST['id_number'].strip():
            id_number = request.POST['id_number'].strip()
            try:
                # Extract DOB from ID number (format: YYMMDD...)
                year = int(id_number[:2])
                month = int(id_number[2:4])
                day = int(id_number[4:6])
                
                # Determine century (00-99)
                current_year = timezone.now().year % 100
                century = 2000 if year <= current_year else 1900
                full_year = century + year
                
                # Check if date is valid
                try:
                    dob = datetime.date(full_year, month, day)
                    # Set the date_of_birth field in the form data
                    official_form.data = official_form.data.copy()
                    official_form.data['date_of_birth'] = dob.isoformat()
                    
                    # Also set gender based on ID number
                    gender_digit = int(id_number[6])
                    official_form.data['gender'] = 'M' if gender_digit >= 5 else 'F'
                except ValueError:
                    # Invalid date in ID number, will be caught in form validation
                    pass
            except (ValueError, IndexError):
                # Invalid ID number, will be caught in form validation
                pass
        
        # Generate a unique email for the official before checking form validity
        if 'first_name' in request.POST and 'last_name' in request.POST:
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']
            
            # Generate unique email using position name as a prefix
            position_id = request.POST.get('position')
            position_prefix = 'official'
            
            if position_id:
                try:
                    from .models import Position
                    position = Position.objects.get(pk=position_id)
                    position_prefix = position.title.lower().replace(' ', '')
                except (Position.DoesNotExist, ValueError):
                    position_prefix = 'official'
            
            # Generate unique email with association name
            association_name = request.user.association.name
            unique_email = f"{position_prefix}.{first_name.lower()}.{last_name.lower()}@{association_name.lower().replace(' ', '')}.safa.net"
            
            # Set the email in the form data
            official_form.data = official_form.data.copy()
            official_form.data['email'] = unique_email
        
        if official_form.is_valid():
            # Generate a unique SAFA ID if one wasn't provided
            if not official_form.cleaned_data.get('safa_id'):
                from .utils import generate_unique_safa_id
                try:
                    unique_safa_id = generate_unique_safa_id()
                    official_form.instance.safa_id = unique_safa_id
                except Exception as e:
                    messages.warning(request, f"Could not generate a unique SAFA ID: {e}")
            
            # Save official without committing to DB yet
            official = official_form.save(commit=False)
            # Link official to the appropriate geographical entities
            official.province = request.user.province
            official.region = request.user.region
            official.local_federation = request.user.local_federation
            # Save the official to get an ID
            official.save()
            
            # Add association to the official's associations
            official.associations.add(request.user.association)
            
            # Create invoice for the official
            from .utils import create_official_invoice
            position = official_form.cleaned_data.get('position')
            position_type = position.title if position else None
            
            invoice = create_official_invoice(
                official=official,
                association=request.user.association,  # Use association instead of club
                issued_by=official,  # Using official as issued_by as they don't have a separate Member instance
                position_type=position_type
            )
            
            # If this is a referee with a level, create a certification record
            referee_level = official_form.cleaned_data.get('referee_level')
            position_title = position.title.lower() if position else ""
            if referee_level and "referee" in position_title:
                from membership.models.main import OfficialCertification
                
                # Create certification record
                certification = OfficialCertification(
                    official=official,
                    certification_type='REFEREE',
                    level=referee_level,
                    name=f"Referee Level {referee_level}",
                    issuing_body="SAFA",
                    certification_number=official_form.cleaned_data.get('certification_number'),
                    obtained_date=timezone.now().date(),
                    expiry_date=official_form.cleaned_data.get('certification_expiry_date'),
                    document=official_form.cleaned_data.get('certification_document'),
                    notes="Initial certification registered with official",
                    is_verified=False  # Requires verification
                )
                certification.save()
            
            success_message = f'Official registered successfully with email {official.email}!'
            if invoice:
                success_message += f' An invoice (#{invoice.invoice_number}) has been created.'
                base_fee = "250" if "referee" in position_title else "200" if "coach" in position_title else "150"
                success_message += f' Registration fee: R{base_fee}.'
                success_message += ' Official will be eligible for approval once the invoice is paid.'
            
            messages.success(request, success_message)
            return redirect('accounts:official_list')
        else:
            # Add a summary error message at the top without showing specific fields
            messages.error(request, 'Please correct the errors in the form below.')
    else:
        official_form = AssociationOfficialRegistrationForm()
    
    return render(request, 'accounts/association_admin_add_official.html', {
        'official_form': official_form
    })
