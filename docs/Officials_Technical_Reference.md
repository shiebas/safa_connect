# Technical Reference: Officials, Certifications and Associations

This document provides technical details about the implementation of the Officials module, including certification history tracking and association memberships.

## Model Structure

### Official Model

The `Official` model extends the base `Member` model and includes:

```python
class Official(Member):
    # Approval status
    is_approved = models.BooleanField(default=False)
    
    # Position in the organization
    position = models.ForeignKey('accounts.Position', on_delete=models.PROTECT, 
                               related_name='officials')
    
    # Basic certification fields (legacy support)
    certification_number = models.CharField(max_length=50, blank=True, null=True)
    certification_document = models.FileField(upload_to='certification_documents/',
                                           blank=True, null=True)
    certification_expiry_date = models.DateField(blank=True, null=True)
    
    # For referees (legacy support)
    referee_level = models.CharField(max_length=20, blank=True, null=True,
                                  choices=[
                                      ('LOCAL', 'Local'),
                                      ('REGIONAL', 'Regional'),
                                      ('PROVINCIAL', 'Provincial'),
                                      ('NATIONAL', 'National'),
                                      ('INTERNATIONAL', 'International'),
                                  ])
    
    # Link to associations (many-to-many)
    associations = models.ManyToManyField('geography.Association', 
                                        related_name='member_officials',
                                        blank=True)
```

### OfficialCertification Model

The `OfficialCertification` model allows tracking multiple certifications for each official:

```python
class OfficialCertification(TimeStampedModel):
    # Link to official
    official = models.ForeignKey(Official, on_delete=models.CASCADE,
                              related_name='certifications')
    
    # Certification type
    certification_type = models.CharField(max_length=20,
                                       choices=[
                                           ('REFEREE', 'Referee Certification'),
                                           ('COACH', 'Coaching Certification'),
                                           ('ADMIN', 'Administrative Certification'),
                                           ('OTHER', 'Other Certification'),
                                       ])
    
    # Certification level
    level = models.CharField(max_length=20, 
                          choices=[
                              ('LOCAL', 'Local'),
                              ('REGIONAL', 'Regional'),
                              ('PROVINCIAL', 'Provincial'),
                              ('NATIONAL', 'National'),
                              ('INTERNATIONAL', 'International'),
                          ])
    
    # Details
    name = models.CharField(max_length=100)
    issuing_body = models.CharField(max_length=100)
    certification_number = models.CharField(max_length=50, blank=True, null=True)
    obtained_date = models.DateField()
    expiry_date = models.DateField(blank=True, null=True)
    
    # Document
    document = models.FileField(upload_to='certification_documents/history/',
                             blank=True, null=True)
    
    # Notes and verification
    notes = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
```

### Position Model

The `Position` model has been refactored to allow the same position name to be used at different levels:

```python
class Position(models.Model):
    # Unique title across all levels
    title = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Levels where this position can be used (comma-separated)
    levels = models.CharField(max_length=100, 
                           default='NATIONAL,PROVINCE,REGION,LFA,CLUB')
    
    # Other fields
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, 
                                null=True, blank=True, 
                                related_name='created_positions')
    requires_approval = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

## Invoice Integration

Officials now trigger automatic invoice creation upon registration:

```python
def create_official_invoice(official, club, issued_by, position_type=None):
    """
    Create an invoice for official registration
    
    Args:
        official (Official): The official to create an invoice for
        club (Club): The club the official is registering with
        issued_by (Member): The admin who issued the invoice
        position_type (str): Type of position - determines fee amount
        
    Returns:
        Invoice: The created invoice
    """
    # Set fee amount based on position type
    fee_amount = 150.00  # Default fee
    position_title = "Standard Position"
    
    if official.position:
        position_title = official.position.title
        # Check if referee or coach for higher fee
        if "referee" in position_title.lower():
            fee_amount = 250.00
        elif "coach" in position_title.lower():
            fee_amount = 200.00
    
    # Generate a reference number
    reference = f"REG-OFF-{official.membership_number or official.id}-{timezone.now().strftime('%Y%m%d')}"

    # Create invoice
    invoice = Invoice(
        invoice_type='REGISTRATION',
        amount=fee_amount,
        status='PENDING',
        issue_date=timezone.now().date(),
        player=None,  # Not a player registration
        official=official,  # Link to official
        club=club,
        issued_by=issued_by,
        reference=reference
    )
    invoice.save()
    
    # Create invoice item
    item = InvoiceItem(
        invoice=invoice,
        description=f"{position_title} Registration Fee",
        quantity=1,
        unit_price=fee_amount,
        sub_total=fee_amount
    )
    item.save()
    
    return invoice
```

## Approval Workflow

The approval process checks that invoices are paid before allowing approval:

```python
@login_required
def approve_official(request, official_id):
    """Approve an official registration"""
    official = get_object_or_404(Official, id=official_id)
    
    # Check permissions
    has_permission = request.user.role in ['ADMIN_LOCAL_FED', 'ADMIN_REGION', 
                                        'ADMIN_PROVINCE', 'ADMIN_NATIONAL'] or request.user.is_superuser
    
    if not has_permission:
        messages.error(request, 'You do not have permission to approve officials.')
        return redirect('accounts:dashboard')
    
    # Check if the official has any unpaid invoices
    unpaid_invoices = Invoice.objects.filter(official=official, 
                                          status__in=['PENDING', 'OVERDUE'])
    
    if unpaid_invoices.exists():
        messages.error(request, 'Official cannot be approved until all registration invoices are paid.')
        return redirect('accounts:official_detail', official_id=official.id)
    
    # Approve the official
    official.is_approved = True
    official.status = 'ACTIVE'
    official.save()
    
    messages.success(request, f'Official {official.get_full_name()} has been approved.')
    return redirect('accounts:official_detail', official_id=official.id)
```

## Key Functions

### Auto-Association with Relevant Bodies

The system automatically associates officials with relevant referee or coaching associations during registration:

```python
# Associate with appropriate referee/coach associations if needed
position_title = position.title.lower() if position else ""
if "referee" in position_title or "coach" in position_title:
    from geography.models import Association
    
    # Find relevant associations by type
    association_type = "referee" if "referee" in position_title else "coach"
    associations = Association.objects.filter(
        type__icontains=association_type,
        local_football_association=request.user.local_federation
    )
    
    # Link to associations
    if associations.exists():
        for association in associations:
            official.associations.add(association)
```

### Initial Certification Creation

For referees, an initial certification record is created during registration:

```python
# If this is a referee with a level, create a certification record
referee_level = official_form.cleaned_data.get('referee_level')
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
```

## URLs

The following URLs are available for managing officials:

```python
# Official management URLs
path('officials/<int:official_id>/', official_detail, name='official_detail'),
path('officials/<int:official_id>/add-certification/', add_official_certification, 
   name='add_official_certification'),
path('officials/<int:official_id>/approve/', approve_official, name='approve_official'),
path('officials/<int:official_id>/unapprove/', unapprove_official, name='unapprove_official'),
path('officials/<int:official_id>/manage-associations/', manage_official_associations, 
   name='manage_official_associations'),
```

## Position Usage Changes

With the updated Position model, positions are now:

1. Uniquely named across all levels
2. Can be used at multiple levels through the `levels` field
3. No longer duplicated for each level of organization

This enables positions like "Secretary" or "Coach" to be defined once and used at any level (club, LFA, province, national), making the system more maintainable and consistent.

The available levels are:
- NATIONAL
- PROVINCE
- REGION
- LFA
- CLUB

## Implementation Considerations

When extending this functionality, consider the following:

1. **Invoice Integration**: Officials cannot be approved until invoices are paid
2. **Certification Verification**: Only admins can verify certifications
3. **Position Management**: Positions should be centrally managed to maintain consistency
4. **Association Linking**: Officials are automatically linked to relevant associations

## Database Migrations

The following migrations were applied:

1. `0002_update_position_titles.py` - Made position titles unique
2. `0003_add_position_levels_field.py` - Added the levels field
3. `0004_remove_position_level_manual.py` - Recorded removal of level field
4. `0005_alter_position_options_and_more.py` - Updated model options

The legacy `level` field was removed from the database table using direct SQL commands to avoid SQLite migration issues.

## API Integration

For API usage, the Official model includes the following serializers:

- `OfficialSerializer` - Basic official details
- `OfficialDetailSerializer` - Detailed information including certifications
- `OfficialCertificationSerializer` - Certification details

## Security Considerations

- Only club admins can add officials to their own club
- Only LFA and higher-level admins can approve officials
- Only admins can verify certifications
- Invoice payment verification is required before approval
