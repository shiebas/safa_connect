# membership/serializers.py - CORRECTED VERSION
# Fully aligned with the new SAFA membership system

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

from .models import (
    Member, SAFASeasonConfig, SAFAFeeStructure, Transfer, 
    Invoice, InvoiceItem, MemberDocument, RegistrationWorkflow,
    MemberSeasonHistory, ClubMemberQuota, OrganizationSeasonRegistration,
    MemberProfile
)
from geography.models import Club, Province, Region, LocalFootballAssociation, Association

User = get_user_model()


class SAFASeasonConfigSerializer(serializers.ModelSerializer):
    """Serializer for SAFA Season Configuration"""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    organization_registration_status = serializers.SerializerMethodField()
    member_registration_status = serializers.SerializerMethodField()
    days_until_member_registration = serializers.SerializerMethodField()
    
    class Meta:
        model = SAFASeasonConfig
        fields = [
            'id', 'season_year', 'season_start_date', 'season_end_date',
            'organization_registration_start', 'organization_registration_end',
            'member_registration_start', 'member_registration_end',
            'vat_rate', 'payment_due_days', 'is_active', 'is_renewal_season',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
            'organization_registration_status', 'member_registration_status',
            'days_until_member_registration'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_organization_registration_status(self, obj):
        return "open" if obj.organization_registration_open else "closed"
    
    def get_member_registration_status(self, obj):
        return "open" if obj.member_registration_open else "closed"
    
    def get_days_until_member_registration(self, obj):
        if obj.member_registration_start:
            today = timezone.now().date()
            if today < obj.member_registration_start:
                return (obj.member_registration_start - today).days
        return None


class SAFAFeeStructureSerializer(serializers.ModelSerializer):
    """Serializer for SAFA Fee Structure"""
    
    entity_type_display = serializers.CharField(source='get_entity_type_display', read_only=True)
    season_year = serializers.IntegerField(source='season_config.season_year', read_only=True)
    annual_fee_with_vat = serializers.SerializerMethodField()
    
    class Meta:
        model = SAFAFeeStructure
        fields = [
            'id', 'season_config', 'season_year', 'entity_type', 'entity_type_display',
            'annual_fee', 'annual_fee_with_vat', 'description', 'is_pro_rata', 'minimum_fee',
            'is_organization', 'requires_organization_payment', 'created_at'
        ]
        read_only_fields = ['is_organization', 'created_at']
    
    def get_annual_fee_with_vat(self, obj):
        if obj.season_config and obj.annual_fee:
            vat_amount = obj.annual_fee * obj.season_config.vat_rate
            return obj.annual_fee + vat_amount
        return obj.annual_fee


class MemberDocumentSerializer(serializers.ModelSerializer):
    """Serializer for Member Documents"""
    
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = MemberDocument
        fields = [
            'id', 'document_type', 'document_type_display', 'document_file',
            'verification_status', 'verification_status_display', 'verified_by',
            'verified_by_name', 'verified_date', 'rejection_notes',
            'file_size', 'file_size_mb', 'file_type', 'is_required', 
            'expiry_date', 'is_expired', 'created', 'modified'
        ]
        read_only_fields = ['file_size', 'file_type', 'verified_by', 'verified_date', 'created', 'modified']
    
    def get_file_size_mb(self, obj):
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return None
    
    def get_is_expired(self, obj):
        if obj.expiry_date:
            return obj.expiry_date < timezone.now().date()
        return False


class RegistrationWorkflowSerializer(serializers.ModelSerializer):
    """Serializer for Registration Workflow"""
    
    current_step_display = serializers.CharField(source='get_current_step_display', read_only=True)
    next_actions = serializers.SerializerMethodField()
    member_name = serializers.CharField(source='member.get_full_name', read_only=True)
    
    class Meta:
        model = RegistrationWorkflow
        fields = [
            'id', 'member', 'member_name', 'personal_info_status', 'club_selection_status',
            'document_upload_status', 'payment_status', 'club_approval_status',
            'safa_approval_status', 'current_step', 'current_step_display',
            'completion_percentage', 'next_actions', 'created', 'modified'
        ]
        read_only_fields = ['completion_percentage', 'current_step', 'created', 'modified']
    
    def get_next_actions(self, obj):
        return obj.get_next_required_actions()


class MemberProfileSerializer(serializers.ModelSerializer):
    """Serializer for Member Profile (role-specific information)"""
    
    official_position_name = serializers.CharField(source='official_position.title', read_only=True)
    
    class Meta:
        model = MemberProfile
        fields = [
            'id', 'player_position', 'official_position', 'official_position_name',
            'certification_number', 'certification_document', 'certification_expiry_date',
            'referee_level', 'guardian_name', 'guardian_email', 'guardian_phone',
            'birth_certificate'
        ]


class AssociationSimpleSerializer(serializers.ModelSerializer):
    """Simple serializer for associations (for nested use)"""
    
    class Meta:
        model = Association
        fields = ['id', 'name', 'association_type']


class MemberSerializer(serializers.ModelSerializer):
    """Enhanced serializer for SAFA Members"""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    age = serializers.IntegerField(read_only=True)
    is_junior = serializers.BooleanField(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    registration_method_display = serializers.CharField(source='get_registration_method_display', read_only=True)
    
    # Related fields
    current_club_name = serializers.CharField(source='current_club.name', read_only=True)
    current_season_year = serializers.IntegerField(source='current_season.season_year', read_only=True)
    province_name = serializers.CharField(source='province.name', read_only=True)
    region_name = serializers.CharField(source='region.name', read_only=True)
    lfa_name = serializers.CharField(source='lfa.name', read_only=True)
    
    # CORRECTED: Multiple associations for officials
    associations = AssociationSimpleSerializer(many=True, read_only=True)
    association_names = serializers.SerializerMethodField()
    
    # Nested serializers (optional, for detailed views)
    documents = MemberDocumentSerializer(many=True, read_only=True)
    workflow = RegistrationWorkflowSerializer(read_only=True)
    profile = MemberProfileSerializer(read_only=True)
    
    # Financial information
    registration_fee = serializers.SerializerMethodField()
    has_outstanding_invoices = serializers.SerializerMethodField()
    
    class Meta:
        model = Member
        fields = [
            'id', 'safa_id', 'full_name', 'first_name', 'last_name', 'email',
            'phone_number', 'date_of_birth', 'age', 'is_junior', 'gender',
            'id_number', 'passport_number', 'nationality',
            'role', 'role_display', 'status', 'status_display',
            'registration_method', 'registration_method_display',
            'registration_complete', 'is_existing_member', 'previous_safa_id',
            'current_club', 'current_club_name', 'current_season', 'current_season_year',
            'province', 'province_name', 'region', 'region_name', 'lfa', 'lfa_name',
            'associations', 'association_names',
            'street_address', 'suburb', 'city', 'state', 'postal_code', 'country',
            'emergency_contact', 'emergency_phone', 'medical_notes',
            'terms_accepted', 'privacy_accepted', 'marketing_consent',
            'approved_by', 'approved_date', 'rejection_reason',
            'registration_fee', 'has_outstanding_invoices',
            'created', 'modified', 'documents', 'workflow', 'profile'
        ]
        read_only_fields = [
            'safa_id', 'age', 'is_junior', 'approved_by', 'approved_date', 
            'created', 'modified', 'registration_fee', 'has_outstanding_invoices'
        ]
    
    def get_association_names(self, obj):
        """Get comma-separated list of association names"""
        if obj.role == 'OFFICIAL':
            return ', '.join([assoc.name for assoc in obj.associations.all()])
        return ''
    
    def get_registration_fee(self, obj):
        """Calculate member's registration fee"""
        try:
            return float(obj.calculate_registration_fee())
        except:
            return 0.0
    
    def get_has_outstanding_invoices(self, obj):
        """Check if member has outstanding invoices"""
        return obj.invoices.filter(status__in=['PENDING', 'OVERDUE', 'PARTIALLY_PAID']).exists()
    
    def validate_email(self, value):
        """Ensure email is unique"""
        if self.instance:
            # Update case - exclude current instance
            if Member.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("A member with this email already exists.")
        else:
            # Create case
            if Member.objects.filter(email=value).exists():
                raise serializers.ValidationError("A member with this email already exists.")
        return value
    
    def validate_id_number(self, value):
        """Validate South African ID number"""
        if value:
            if len(value) != 13 or not value.isdigit():
                raise serializers.ValidationError("ID number must be exactly 13 digits.")
            
            # Check uniqueness
            if self.instance:
                if Member.objects.filter(id_number=value).exclude(pk=self.instance.pk).exists():
                    raise serializers.ValidationError("A member with this ID number already exists.")
            else:
                if Member.objects.filter(id_number=value).exists():
                    raise serializers.ValidationError("A member with this ID number already exists.")
        return value
    
    def validate_current_club(self, value):
        """Validate club selection"""
        if not value:
            raise serializers.ValidationError("Club selection is mandatory.")
        return value


class MemberSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for member lists and search results"""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    current_club_name = serializers.CharField(source='current_club.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = Member
        fields = [
            'id', 'safa_id', 'full_name', 'email', 'status', 'status_display',
            'role', 'role_display', 'current_club_name', 'registration_complete',
            'created'
        ]


class InvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer for Invoice Items"""
    
    sub_total = serializers.SerializerMethodField()
    
    class Meta:
        model = InvoiceItem
        fields = ['id', 'description', 'quantity', 'unit_price', 'sub_total']
        
    def get_sub_total(self, obj):
        return obj.quantity * obj.unit_price


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoices"""
    
    invoice_type_display = serializers.CharField(source='get_invoice_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    season_year = serializers.IntegerField(source='season_config.season_year', read_only=True)
    
    # Billed to information
    billed_to_name = serializers.SerializerMethodField()
    billed_to_type = serializers.SerializerMethodField()
    
    # Financial calculations
    outstanding_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    payment_percentage = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    days_overdue = serializers.SerializerMethodField()
    
    # Line items
    items = InvoiceItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'uuid', 'invoice_number', 'season_config', 'season_year',
            'invoice_type', 'invoice_type_display', 'status', 'status_display',
            'subtotal', 'vat_rate', 'vat_amount', 'total_amount',
            'paid_amount', 'outstanding_amount', 'payment_percentage',
            'issue_date', 'due_date', 'payment_date', 'is_overdue', 'days_overdue',
            'payment_method', 'payment_reference', 'notes', 'is_payment_plan',
            'installments', 'billed_to_name', 'billed_to_type', 'items',
            'created', 'modified'
        ]
        read_only_fields = [
            'uuid', 'invoice_number', 'vat_amount', 'total_amount',
            'outstanding_amount', 'payment_percentage', 'is_overdue',
            'days_overdue', 'created', 'modified'
        ]
    
    def get_billed_to_name(self, obj):
        if obj.member:
            return obj.member.get_full_name()
        elif obj.organization:
            return getattr(obj.organization, 'name', str(obj.organization))
        return 'Unknown'
    
    def get_billed_to_type(self, obj):
        if obj.member:
            return 'Member'
        elif obj.organization:
            return 'Organization'
        return 'Unknown'
    
    def get_payment_percentage(self, obj):
        if hasattr(obj, 'payment_percentage'):
            return obj.payment_percentage
        if obj.total_amount > 0:
            return round((obj.paid_amount / obj.total_amount * 100), 2)
        return 0
    
    def get_is_overdue(self, obj):
        if hasattr(obj, 'is_overdue'):
            return obj.is_overdue
        return (obj.due_date and obj.due_date < timezone.now().date() 
                and obj.status in ['PENDING', 'PARTIALLY_PAID'])
    
    def get_days_overdue(self, obj):
        if self.get_is_overdue(obj) and obj.due_date:
            return (timezone.now().date() - obj.due_date).days
        return 0


class TransferSerializer(serializers.ModelSerializer):
    """Serializer for Member Transfers"""
    
    member_name = serializers.CharField(source='member.get_full_name', read_only=True)
    member_safa_id = serializers.CharField(source='member.safa_id', read_only=True)
    from_club_name = serializers.CharField(source='from_club.name', read_only=True)
    to_club_name = serializers.CharField(source='to_club.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    days_pending = serializers.SerializerMethodField()
    can_approve = serializers.SerializerMethodField()
    
    class Meta:
        model = Transfer
        fields = [
            'id', 'member', 'member_name', 'member_safa_id',
            'from_club', 'from_club_name', 'to_club', 'to_club_name',
            'request_date', 'effective_date', 'status', 'status_display',
            'reason', 'transfer_fee', 'approved_by', 'approved_by_name',
            'approved_date', 'rejection_reason', 'days_pending', 'can_approve',
            'created', 'modified'
        ]
        read_only_fields = [
            'approved_by', 'approved_date', 'effective_date', 
            'days_pending', 'can_approve', 'created', 'modified'
        ]
    
    def get_days_pending(self, obj):
        if obj.status == 'PENDING':
            return (timezone.now().date() - obj.request_date).days
        return None
    
    def get_can_approve(self, obj):
        """Check if current user can approve this transfer"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return request.user.is_staff or request.user.is_superuser
        return False
    
    def validate(self, data):
        """Validate transfer request"""
        member = data.get('member')
        from_club = data.get('from_club')
        to_club = data.get('to_club')
        
        if member and from_club and member.current_club != from_club:
            raise serializers.ValidationError(
                "Member's current club must match the transfer source club"
            )
        
        if from_club and to_club and from_club == to_club:
            raise serializers.ValidationError(
                "Cannot transfer member to the same club"
            )
        
        # Check for existing pending transfers
        if member and Transfer.objects.filter(
            member=member, 
            status='PENDING'
        ).exclude(pk=getattr(self.instance, 'pk', None)).exists():
            raise serializers.ValidationError(
                "Member already has a pending transfer request"
            )
        
        return data


class MemberSeasonHistorySerializer(serializers.ModelSerializer):
    """Serializer for Member Season History"""
    
    member_name = serializers.CharField(source='member.get_full_name', read_only=True)
    member_safa_id = serializers.CharField(source='member.safa_id', read_only=True)
    season_year = serializers.IntegerField(source='season_config.season_year', read_only=True)
    club_name = serializers.CharField(source='club.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    transferred_from_club_name = serializers.CharField(source='transferred_from_club.name', read_only=True)
    association_names = serializers.SerializerMethodField()
    
    class Meta:
        model = MemberSeasonHistory
        fields = [
            'id', 'member', 'member_name', 'member_safa_id',
            'season_config', 'season_year', 'status', 'status_display',
            'club', 'club_name', 'registration_date', 'registration_method',
            'invoice_paid', 'safa_approved', 'safa_approved_date',
            'jersey_number', 'position', 'transferred_from_club',
            'transferred_from_club_name', 'transfer_date', 'association_names',
            'created', 'modified'
        ]
        read_only_fields = ['member', 'season_config', 'created', 'modified']
    
    def get_association_names(self, obj):
        """Get comma-separated list of association names for this season"""
        return ', '.join([assoc.name for assoc in obj.associations.all()])


class ClubMemberQuotaSerializer(serializers.ModelSerializer):
    """Serializer for Club Member Quotas"""
    
    club_name = serializers.CharField(source='club.name', read_only=True)
    season_year = serializers.IntegerField(source='season_config.season_year', read_only=True)
    
    # Utilization percentages
    senior_utilization = serializers.SerializerMethodField()
    junior_utilization = serializers.SerializerMethodField()
    officials_utilization = serializers.SerializerMethodField()
    total_utilization = serializers.SerializerMethodField()
    
    # Availability status
    can_register_senior = serializers.SerializerMethodField()
    can_register_junior = serializers.SerializerMethodField()
    can_register_official = serializers.SerializerMethodField()
    
    class Meta:
        model = ClubMemberQuota
        fields = [
            'id', 'club', 'club_name', 'season_config', 'season_year',
            'max_senior_players', 'current_senior_players', 'senior_utilization', 'can_register_senior',
            'max_junior_players', 'current_junior_players', 'junior_utilization', 'can_register_junior',
            'max_officials', 'current_officials', 'officials_utilization', 'can_register_official',
            'total_utilization'
        ]
        read_only_fields = [
            'current_senior_players', 'current_junior_players', 'current_officials'
        ]
    
    def get_senior_utilization(self, obj):
        if obj.max_senior_players > 0:
            return round((obj.current_senior_players / obj.max_senior_players) * 100, 1)
        return 0
    
    def get_junior_utilization(self, obj):
        if obj.max_junior_players > 0:
            return round((obj.current_junior_players / obj.max_junior_players) * 100, 1)
        return 0
    
    def get_officials_utilization(self, obj):
        if obj.max_officials > 0:
            return round((obj.current_officials / obj.max_officials) * 100, 1)
        return 0
    
    def get_total_utilization(self, obj):
        total_max = obj.max_senior_players + obj.max_junior_players + obj.max_officials
        total_current = obj.current_senior_players + obj.current_junior_players + obj.current_officials
        if total_max > 0:
            return round((total_current / total_max) * 100, 1)
        return 0
    
    def get_can_register_senior(self, obj):
        return obj.can_register_member('senior_player')
    
    def get_can_register_junior(self, obj):
        return obj.can_register_member('junior_player')
    
    def get_can_register_official(self, obj):
        return obj.can_register_member('official')


class OrganizationSeasonRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for Organization Season Registration"""
    
    organization_name = serializers.CharField(source='organization_name', read_only=True)
    organization_type = serializers.CharField(source='organization_type', read_only=True)
    season_year = serializers.IntegerField(source='season_config.season_year', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    invoice_amount = serializers.DecimalField(
        source='invoice.total_amount', 
        max_digits=12, 
        decimal_places=2, 
        read_only=True
    )
    registered_by_name = serializers.CharField(source='registered_by.get_full_name', read_only=True)
    can_register_members = serializers.SerializerMethodField()
    
    class Meta:
        model = OrganizationSeasonRegistration
        fields = [
            'id', 'season_config', 'season_year', 'organization_name',
            'organization_type', 'registration_date', 'status', 'status_display',
            'invoice', 'invoice_number', 'invoice_amount', 'registered_by',
            'registered_by_name', 'can_register_members', 'created', 'modified'
        ]
        read_only_fields = [
            'organization_name', 'organization_type', 'registered_by',
            'can_register_members', 'created', 'modified'
        ]
    
    def get_can_register_members(self, obj):
        return obj.can_register_members()


# ============================================================================
# SPECIALIZED SERIALIZERS FOR API ENDPOINTS
# ============================================================================

class MemberRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for member registration API endpoint"""
    
    # Additional validation fields
    confirm_email = serializers.EmailField(write_only=True)
    terms_accepted = serializers.BooleanField(required=True)
    privacy_accepted = serializers.BooleanField(required=True)
    
    # CORRECTED: Multiple associations for officials
    associations = serializers.PrimaryKeyRelatedField(
        queryset=Association.objects.all(),
        many=True,
        required=False,
        help_text="Select associations if you are an official"
    )
    
    class Meta:
        model = Member
        fields = [
            'first_name', 'last_name', 'email', 'confirm_email',
            'phone_number', 'date_of_birth', 'gender', 'id_number',
            'passport_number', 'nationality', 'role', 'current_club',
            'associations', 'street_address', 'suburb', 'city', 'state', 
            'postal_code', 'country', 'emergency_contact', 'emergency_phone', 
            'medical_notes', 'terms_accepted', 'privacy_accepted', 'marketing_consent'
        ]
    
    def validate(self, data):
        """Validate registration data"""
        # Check email confirmation
        if data.get('email') != data.get('confirm_email'):
            raise serializers.ValidationError("Email addresses do not match")
        
        # Ensure either ID number or passport is provided
        if not data.get('id_number') and not data.get('passport_number'):
            raise serializers.ValidationError(
                "Either ID number or passport number is required"
            )
        
        # Check terms acceptance
        if not data.get('terms_accepted'):
            raise serializers.ValidationError("Terms and conditions must be accepted")
        
        if not data.get('privacy_accepted'):
            raise serializers.ValidationError("Privacy policy must be accepted")
        
        # CORRECTED: Validate associations for officials
        role = data.get('role')
        associations = data.get('associations', [])
        
        if role == 'OFFICIAL' and not associations:
            raise serializers.ValidationError("Officials must select at least one association")
        elif role != 'OFFICIAL' and associations:
            raise serializers.ValidationError("Only officials can select associations")
        
        # Remove confirm_email from validated data
        data.pop('confirm_email', None)
        
        return data
    
    def create(self, validated_data):
        """Create new member with additional setup"""
        # Extract associations before creating member
        associations = validated_data.pop('associations', [])
        
        # Set registration method and season
        validated_data['registration_method'] = 'SELF'
        validated_data['current_season'] = SAFASeasonConfig.get_active_season()
        
        member = super().create(validated_data)
        
        # Set associations for officials
        if member.role == 'OFFICIAL' and associations:
            member.associations.set(associations)
        
        return member


class InvoicePaymentSerializer(serializers.Serializer):
    """Serializer for invoice payment processing"""
    
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    payment_method = serializers.ChoiceField(choices=[
        ('EFT', 'Electronic Funds Transfer'),
        ('CARD', 'Credit Card'),
        ('CASH', 'Cash'),
        ('CHEQUE', 'Cheque'),
        ('OTHER', 'Other')
    ])
    payment_reference = serializers.CharField(max_length=100, required=False)
    notes = serializers.CharField(max_length=500, required=False)
    
    def validate_amount(self, value):
        """Validate payment amount against invoice"""
        if hasattr(self, 'instance') and self.instance:
            outstanding = getattr(self.instance, 'outstanding_amount', 
                                self.instance.total_amount - self.instance.paid_amount)
            if value > outstanding:
                raise serializers.ValidationError(
                    f"Payment amount cannot exceed outstanding amount of R{outstanding}"
                )
        return value


class MemberSearchSerializer(serializers.Serializer):
    """Serializer for member search parameters"""
    
    query = serializers.CharField(max_length=100, required=False)
    status = serializers.ChoiceField(choices=Member.MEMBERSHIP_STATUS, required=False)
    role = serializers.ChoiceField(choices=Member.MEMBER_ROLES, required=False)
    club = serializers.IntegerField(required=False)
    season = serializers.IntegerField(required=False)
    province = serializers.IntegerField(required=False)
    region = serializers.IntegerField(required=False)
    lfa = serializers.IntegerField(required=False)
    registration_method = serializers.ChoiceField(choices=Member.REGISTRATION_METHODS, required=False)
    
    # Date range filters
    created_after = serializers.DateField(required=False)
    created_before = serializers.DateField(required=False)
    
    # Pagination
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=20)


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    
    # Member statistics
    total_members = serializers.IntegerField()
    active_members = serializers.IntegerField()
    pending_members = serializers.IntegerField()
    rejected_members = serializers.IntegerField()
    inactive_members = serializers.IntegerField()
    
    # Role breakdown
    total_players = serializers.IntegerField()
    total_officials = serializers.IntegerField()
    total_admins = serializers.IntegerField()
    
    # Invoice statistics
    total_invoices = serializers.IntegerField()
    paid_invoices = serializers.IntegerField()
    pending_invoices = serializers.IntegerField()
    overdue_invoices = serializers.IntegerField()
    
    # Financial statistics
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    outstanding_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    collection_rate = serializers.FloatField()
    
    # Transfer statistics
    pending_transfers = serializers.IntegerField()
    approved_transfers = serializers.IntegerField()
    rejected_transfers = serializers.IntegerField()
    
    # Season information
    active_season = SAFASeasonConfigSerializer(required=False)
    
    # Trends (optional)
    member_growth_rate = serializers.FloatField(required=False)
    average_invoice_value = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)


class SystemHealthSerializer(serializers.Serializer):
    """Serializer for system health check data"""
    
    status = serializers.ChoiceField(choices=['healthy', 'warning', 'error'])
    
    # Data integrity checks
    total_members = serializers.IntegerField()
    members_without_clubs = serializers.IntegerField()
    members_without_seasons = serializers.IntegerField()
    members_with_invalid_ids = serializers.IntegerField()
    
    # Invoice integrity
    invoices_without_items = serializers.IntegerField()
    invoices_with_calculation_errors = serializers.IntegerField()
    
    # Workflow integrity
    workflows_incomplete = serializers.IntegerField()
    orphaned_workflows = serializers.IntegerField()
    
    # Club quotas
    clubs_without_quotas = serializers.IntegerField()
    clubs_over_quota = serializers.IntegerField()
    
    # Overall health score
    data_integrity_score = serializers.FloatField(min_value=0, max_value=100)
    
    # Detailed issues
    issues = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        ),
        required=False
    )
    
    # Recommendations
    recommendations = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )


# ============================================================================
# UTILITY SERIALIZERS
# ============================================================================

class ChoiceFieldSerializer(serializers.Serializer):
    """Generic serializer for choice fields"""
    
    value = serializers.CharField()
    display = serializers.CharField()


class FileUploadSerializer(serializers.Serializer):
    """Serializer for file upload operations"""
    
    file = serializers.FileField()
    document_type = serializers.ChoiceField(choices=MemberDocument.DOCUMENT_TYPES)
    is_required = serializers.BooleanField(default=False)
    expiry_date = serializers.DateField(required=False)
    
    def validate_file(self, value):
        """Validate uploaded file"""
        # Check file size (5MB limit)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("File size must be less than 5MB")
        
        # Check file type
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Only PDF, JPG, and PNG files are allowed")
        
        return value


class BulkActionSerializer(serializers.Serializer):
    """Serializer for bulk actions"""
    
    action = serializers.ChoiceField(choices=[
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('activate', 'Activate'),
        ('deactivate', 'Deactivate'),
        ('generate_invoices', 'Generate Invoices'),
        ('send_reminders', 'Send Email Reminders')
    ])
    member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100
    )
    reason = serializers.CharField(max_length=500, required=False)
    send_notification = serializers.BooleanField(default=True)
    
    def validate_member_ids(self, value):
        """Validate that all member IDs exist"""
        existing_ids = set(Member.objects.filter(id__in=value).values_list('id', flat=True))
        invalid_ids = set(value) - existing_ids
        
        if invalid_ids:
            raise serializers.ValidationError(
                f"Invalid member IDs: {', '.join(map(str, invalid_ids))}"
            )
        
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        action = data.get('action')
        reason = data.get('reason')
        
        # Reason is required for rejection actions
        if action == 'reject' and not reason:
            raise serializers.ValidationError("Reason is required for rejection actions")
        
        return data


class GeographicHierarchySerializer(serializers.Serializer):
    """Serializer for geographic hierarchy data"""
    
    provinces = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    regions = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    lfas = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    clubs = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )


class ValidationErrorSerializer(serializers.Serializer):
    """Serializer for standardized error responses"""
    
    field = serializers.CharField()
    message = serializers.CharField()
    code = serializers.CharField(required=False)


class APIResponseSerializer(serializers.Serializer):
    """Standardized API response serializer"""
    
    success = serializers.BooleanField()
    message = serializers.CharField(required=False)
    data = serializers.JSONField(required=False)
    errors = ValidationErrorSerializer(many=True, required=False)
    pagination = serializers.DictField(required=False)


class ReportDataSerializer(serializers.Serializer):
    """Serializer for report data"""
    
    report_type = serializers.CharField()
    generated_at = serializers.DateTimeField()
    parameters = serializers.DictField()
    total_records = serializers.IntegerField()
    data = serializers.JSONField()
    export_formats = serializers.ListField(
        child=serializers.CharField()
    )


class NotificationSerializer(serializers.Serializer):
    """Serializer for notifications"""
    
    NOTIFICATION_TYPES = [
        ('registration_approved', 'Registration Approved'),
        ('registration_rejected', 'Registration Rejected'),
        ('invoice_generated', 'Invoice Generated'),
        ('payment_received', 'Payment Received'),
        ('transfer_approved', 'Transfer Approved'),
        ('document_approved', 'Document Approved'),
        ('reminder', 'Payment Reminder'),
    ]
    
    notification_type = serializers.ChoiceField(choices=NOTIFICATION_TYPES)
    recipient_email = serializers.EmailField()
    subject = serializers.CharField(max_length=200)
    message = serializers.CharField()
    send_immediately = serializers.BooleanField(default=True)
    
    # Template variables
    member_name = serializers.CharField(required=False)
    invoice_number = serializers.CharField(required=False)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    due_date = serializers.DateField(required=False)