# membership/api_views.py - API Views for SAFA Membership System
# Clean, properly organized implementation

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings

from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

import json
from decimal import Decimal
from datetime import datetime, timedelta, date
import logging

# Import models
from .models import (
    Member, SAFASeasonConfig, SAFAFeeStructure, Transfer, Invoice, 
    InvoiceItem, MemberDocument, RegistrationWorkflow, MemberSeasonHistory,
    ClubMemberQuota, OrganizationSeasonRegistration
)
from geography.models import Province, Region, LocalFootballAssociation, Club, Association

# Import serializers
from .serializers import (
    MemberSerializer, MemberSummarySerializer, MemberRegistrationSerializer,
    TransferSerializer, InvoiceSerializer, MemberDocumentSerializer,
    RegistrationWorkflowSerializer, SAFASeasonConfigSerializer,
    DashboardStatsSerializer, SystemHealthSerializer, BulkActionSerializer,
    InvoicePaymentSerializer, MemberSearchSerializer
)

logger = logging.getLogger(__name__)


# ============================================================================
# FEE CALCULATION API
# ============================================================================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def calculate_fees(request):
    """Calculate registration fees for members"""
    role = request.GET.get('role')
    date_of_birth = request.GET.get('date_of_birth')
    season_id = request.GET.get('season_id')
    
    if not role:
        return Response({
            'success': False,
            'message': 'Role is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get season
    if season_id:
        try:
            season = SAFASeasonConfig.objects.get(pk=season_id)
        except SAFASeasonConfig.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Season not found'
            }, status=status.HTTP_404_NOT_FOUND)
    else:
        season = SAFASeasonConfig.get_active_season()
        if not season:
            return Response({
                'success': False,
                'message': 'No active season found'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # Determine entity type for fee calculation
    entity_type = 'PLAYER_SENIOR'  # Default
    
    if role == 'PLAYER' and date_of_birth:
        try:
            birth_date = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            age = (timezone.now().date() - birth_date).days // 365
            entity_type = 'PLAYER_JUNIOR' if age < 18 else 'PLAYER_SENIOR'
        except ValueError:
            pass
    elif role == 'OFFICIAL':
        entity_type = 'OFFICIAL_GENERAL'
    
    # Get fee structure
    try:
        fee_structure = SAFAFeeStructure.objects.get(
            season_config=season,
            entity_type=entity_type
        )
    except SAFAFeeStructure.DoesNotExist:
        return Response({
            'success': False,
            'message': f'No fee structure found for {entity_type} in {season.season_year}'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Calculate fees
    base_fee = fee_structure.annual_fee
    vat_amount = base_fee * season.vat_rate
    total_fee = base_fee + vat_amount
    
    # Check for pro-rata calculation
    pro_rata_fee = None
    if fee_structure.is_pro_rata:
        today = timezone.now().date()
        if today > season.season_start_date:
            season_days = (season.season_end_date - season.season_start_date).days
            remaining_days = (season.season_end_date - today).days
            
            if remaining_days > 0:
                pro_rata_base = base_fee * (remaining_days / season_days)
                if fee_structure.minimum_fee:
                    pro_rata_base = max(pro_rata_base, fee_structure.minimum_fee)
                pro_rata_vat = pro_rata_base * season.vat_rate
                pro_rata_fee = pro_rata_base + pro_rata_vat
    
    return Response({
        'success': True,
        'data': {
            'entity_type': entity_type,
            'entity_type_display': fee_structure.get_entity_type_display(),
            'season_year': season.season_year,
            'base_fee': float(base_fee),
            'vat_rate': float(season.vat_rate),
            'vat_amount': float(vat_amount),
            'total_fee': float(total_fee),
            'pro_rata_applicable': fee_structure.is_pro_rata,
            'pro_rata_fee': float(pro_rata_fee) if pro_rata_fee else None,
            'minimum_fee': float(fee_structure.minimum_fee) if fee_structure.minimum_fee else None,
            'description': fee_structure.description,
        }
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics"""
    current_season = SAFASeasonConfig.get_active_season()
    
    if not current_season:
        return Response({
            'success': False,
            'message': 'No active season found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Member statistics
    members_qs = Member.objects.filter(current_season=current_season)
    
    member_stats = {
        'total_members': members_qs.count(),
        'active_members': members_qs.filter(status='ACTIVE').count(),
        'pending_members': members_qs.filter(status='PENDING').count(),
        'rejected_members': members_qs.filter(status='REJECTED').count(),
        'inactive_members': members_qs.filter(status='INACTIVE').count(),
    }
    
    # Role breakdown
    role_stats = {
        'total_players': members_qs.filter(role='PLAYER').count(),
        'total_officials': members_qs.filter(role='OFFICIAL').count(),
        'total_admins': members_qs.filter(role='ADMIN').count(),
    }
    
    # Invoice statistics
    invoices_qs = Invoice.objects.filter(season_config=current_season)
    
    invoice_stats = {
        'total_invoices': invoices_qs.count(),
        'paid_invoices': invoices_qs.filter(status='PAID').count(),
        'pending_invoices': invoices_qs.filter(status='PENDING').count(),
        'overdue_invoices': invoices_qs.filter(status='OVERDUE').count(),
    }
    
    # Financial statistics
    financial_stats = {
        'total_revenue': float(invoices_qs.filter(status='PAID').aggregate(
            total=Sum('total_amount')
        )['total'] or 0),
        'outstanding_revenue': float(invoices_qs.filter(
            status__in=['PENDING', 'OVERDUE', 'PARTIALLY_PAID']
        ).aggregate(
            total=Sum('outstanding_amount')
        )['total'] or 0),
    }
    
    # Calculate collection rate
    total_invoiced = float(invoices_qs.aggregate(total=Sum('total_amount'))['total'] or 0)
    if total_invoiced > 0:
        financial_stats['collection_rate'] = round(
            (financial_stats['total_revenue'] / total_invoiced) * 100, 2
        )
    else:
        financial_stats['collection_rate'] = 0.0
    
    # Transfer statistics
    transfers_qs = Transfer.objects.filter(
        member__current_season=current_season
    )
    
    transfer_stats = {
        'pending_transfers': transfers_qs.filter(status='PENDING').count(),
        'approved_transfers': transfers_qs.filter(status='APPROVED').count(),
        'rejected_transfers': transfers_qs.filter(status='REJECTED').count(),
    }
    
    # Growth rate calculation (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_members = members_qs.filter(created__gte=thirty_days_ago).count()
    previous_total = members_qs.filter(created__lt=thirty_days_ago).count()
    
    if previous_total > 0:
        growth_rate = round(((recent_members / previous_total) * 100), 2)
    else:
        growth_rate = 0.0
    
    # Average invoice value
    avg_invoice = invoices_qs.aggregate(avg=Avg('total_amount'))['avg']
    avg_invoice_value = float(avg_invoice) if avg_invoice else 0.0
    
    stats = {
        **member_stats,
        **role_stats,
        **invoice_stats,
        **financial_stats,
        **transfer_stats,
        'active_season': SAFASeasonConfigSerializer(current_season).data,
        'member_growth_rate': growth_rate,
        'average_invoice_value': round(avg_invoice_value, 2),
    }
    
    return Response({
        'success': True,
        'data': stats
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_charts(request):
    """Get dashboard chart data"""
    current_season = SAFASeasonConfig.get_active_season()
    
    if not current_season:
        return Response({
            'success': False,
            'message': 'No active season found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Member registration over time (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    daily_registrations = Member.objects.filter(
        current_season=current_season,
        created__gte=thirty_days_ago
    ).extra(
        select={'day': 'date(created)'}
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # Status distribution
    status_distribution = Member.objects.filter(
        current_season=current_season
    ).values('status').annotate(
        count=Count('id')
    )
    
    # Role distribution
    role_distribution = Member.objects.filter(
        current_season=current_season
    ).values('role').annotate(
        count=Count('id')
    )
    
    # Monthly registration trends (last 12 months)
    twelve_months_ago = timezone.now() - timedelta(days=365)
    
    monthly_registrations = Member.objects.filter(
        current_season=current_season,
        created__gte=twelve_months_ago
    ).extra(
        select={'month': "DATE_FORMAT(created, '%%Y-%%m')"}
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Invoice status distribution
    invoice_status_distribution = Invoice.objects.filter(
        season_config=current_season
    ).values('status').annotate(
        count=Count('id'),
        total_amount=Sum('total_amount')
    )
    
    # Club membership distribution (top 10 clubs by member count)
    club_distribution = Member.objects.filter(
        current_season=current_season,
        status='ACTIVE'
    ).values(
        'current_club__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Revenue over time (monthly)
    monthly_revenue = Invoice.objects.filter(
        season_config=current_season,
        status='PAID'
    ).extra(
        select={'month': "DATE_FORMAT(payment_date, '%%Y-%%m')"}
    ).values('month').annotate(
        revenue=Sum('total_amount')
    ).order_by('month')
    
    charts = {
        'daily_registrations': [
            {
                'date': item['day'].isoformat() if item['day'] else '',
                'count': item['count']
            } for item in daily_registrations
        ],
        'status_distribution': [
            {
                'status': item['status'],
                'count': item['count']
            } for item in status_distribution
        ],
        'role_distribution': [
            {
                'role': item['role'],
                'count': item['count']
            } for item in role_distribution
        ],
        'monthly_registrations': [
            {
                'month': item['month'],
                'count': item['count']
            } for item in monthly_registrations
        ],
        'invoice_status_distribution': [
            {
                'status': item['status'],
                'count': item['count'],
                'total_amount': float(item['total_amount'] or 0)
            } for item in invoice_status_distribution
        ],
        'club_distribution': [
            {
                'club_name': item['current_club__name'] or 'No Club',
                'member_count': item['count']
            } for item in club_distribution
        ],
        'monthly_revenue': [
            {
                'month': item['month'],
                'revenue': float(item['revenue'] or 0)
            } for item in monthly_revenue
        ]
    }
    
    return Response({
        'success': True,
        'data': charts
    })


# ============================================================================
# PAGINATION CLASS
# ============================================================================

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ============================================================================
# GEOGRAPHIC API ENDPOINTS (for cascading dropdowns)
# ============================================================================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def regions_by_province(request, province_id):
    """Get regions for a given province"""
    try:
        province = get_object_or_404(Province, pk=province_id)
        regions = Region.objects.filter(
            province=province, 
            is_active=True
        ).values('id', 'name').order_by('name')
        return Response(list(regions))
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def lfas_by_region(request, region_id):
    """Get LFAs for a given region"""
    try:
        region = get_object_or_404(Region, pk=region_id)
        lfas = LocalFootballAssociation.objects.filter(
            region=region, 
            is_active=True
        ).values('id', 'name').order_by('name')
        return Response(list(lfas))
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def clubs_by_lfa(request, lfa_id):
    """Get clubs for a given LFA"""
    try:
        lfa = get_object_or_404(LocalFootballAssociation, pk=lfa_id)
        clubs = Club.objects.filter(
            lfa=lfa, 
            is_active=True
        ).values('id', 'name').order_by('name')
        return Response(list(clubs))
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_clubs_by_geography(request):
    """Get clubs filtered by geographic parameters"""
    province_id = request.GET.get('province_id')
    region_id = request.GET.get('region_id')
    lfa_id = request.GET.get('lfa_id')
    
    clubs_qs = Club.objects.filter(is_active=True)
    
    if lfa_id:
        clubs_qs = clubs_qs.filter(lfa_id=lfa_id)
    elif region_id:
        clubs_qs = clubs_qs.filter(region_id=region_id)
    elif province_id:
        clubs_qs = clubs_qs.filter(province_id=province_id)
    
    clubs = clubs_qs.values('id', 'name', 'short_name').order_by('name')
    return Response(list(clubs))


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_associations_by_type(request):
    """Get associations filtered by type"""
    association_type = request.GET.get('type', 'REFEREE')
    
    associations = Association.objects.filter(
        association_type=association_type,
        is_active=True
    ).values('id', 'name', 'association_type').order_by('name')
    
    return Response(list(associations))


class GeographicHierarchyAPIView(APIView):
    """Get complete geographic hierarchy data"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        # Get all active geographic entities
        provinces = Province.objects.filter(is_active=True).values(
            'id', 'name', 'code'
        ).order_by('name')
        
        regions = Region.objects.filter(is_active=True).values(
            'id', 'name', 'province_id', 'province__name'
        ).order_by('province__name', 'name')
        
        lfas = LocalFootballAssociation.objects.filter(is_active=True).values(
            'id', 'name', 'region_id', 'region__name', 'region__province__name'
        ).order_by('region__province__name', 'region__name', 'name')
        
        clubs = Club.objects.filter(is_active=True).values(
            'id', 'name', 'short_name', 'lfa_id', 'region_id', 'province_id'
        ).order_by('province__name', 'region__name', 'lfa__name', 'name')
        
        return Response({
            'success': True,
            'data': {
                'provinces': list(provinces),
                'regions': list(regions),
                'lfas': list(lfas),
                'clubs': list(clubs),
            }
        })


# ============================================================================
# MEMBER API ENDPOINTS
# ============================================================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def member_search(request):
    """Advanced member search with pagination"""
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    role_filter = request.GET.get('role', '')
    club_id = request.GET.get('club', '')
    season_id = request.GET.get('season', '')
    province_id = request.GET.get('province', '')
    
    # Base queryset with permissions
    members_qs = Member.objects.select_related(
        'current_club', 'current_season', 'province', 'region', 'lfa'
    ).prefetch_related('associations')
    
    # Apply user permissions
    user = request.user
    if not (user.is_superuser or user.is_staff):
        try:
            member_profile = user.member_profile
            if hasattr(member_profile, 'current_club') and member_profile.current_club:
                members_qs = members_qs.filter(current_club=member_profile.current_club)
            else:
                return Response({'results': []})
        except AttributeError:
            return Response({'results': []})
    
    # Apply search filters
    if query:
        members_qs = members_qs.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(safa_id__icontains=query) |
            Q(id_number__icontains=query)
        )
    
    if status_filter:
        members_qs = members_qs.filter(status=status_filter)
    
    if role_filter:
        members_qs = members_qs.filter(role=role_filter)
    
    if club_id:
        members_qs = members_qs.filter(current_club_id=club_id)
    
    if season_id:
        members_qs = members_qs.filter(current_season_id=season_id)
    
    if province_id:
        members_qs = members_qs.filter(province_id=province_id)
    
    # Pagination
    paginator = Paginator(members_qs, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Serialize results
    serializer = MemberSummarySerializer(page_obj, many=True)
    
    return Response({
        'results': serializer.data,
        'pagination': {
            'page': page_obj.number,
            'pages': paginator.num_pages,
            'per_page': paginator.per_page,
            'total': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def check_email_availability(request):
    """Check if email is available for registration"""
    email = request.GET.get('email', '').strip().lower()
    
    if not email:
        return Response({
            'is_available': False,
            'message': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    is_taken = Member.objects.filter(email__iexact=email).exists()
    
    return Response({
        'is_available': not is_taken,
        'message': 'Email is already registered' if is_taken else 'Email is available'
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def validate_id_number(request):
    """Validate South African ID number"""
    id_number = request.GET.get('id_number', '').strip()
    
    if not id_number:
        return Response({
            'is_valid': False,
            'message': 'ID number is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check format
    if len(id_number) != 13 or not id_number.isdigit():
        return Response({
            'is_valid': False,
            'message': 'ID number must be exactly 13 digits'
        })
    
    # Check if already exists
    is_taken = Member.objects.filter(id_number=id_number).exists()
    if is_taken:
        return Response({
            'is_valid': False,
            'message': 'ID number is already registered'
        })
    
    # Extract information from ID
    try:
        year = int(id_number[:2])
        month = int(id_number[2:4])
        day = int(id_number[4:6])
        
        # Determine century
        if year < 25:
            year += 2000
        else:
            year += 1900
        
        # Extract gender
        gender_digit = int(id_number[6])
        gender = 'M' if gender_digit >= 5 else 'F'
        
        birth_date = date(year, month, day)
        
        return Response({
            'is_valid': True,
            'message': 'Valid ID number',
            'extracted_info': {
                'birth_date': birth_date.isoformat(),
                'gender': gender,
                'age': (timezone.now().date() - birth_date).days // 365
            }
        })
        
    except (ValueError, IndexError):
        return Response({
            'is_valid': False,
            'message': 'Invalid ID number format'
        })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def club_search(request):
    """Search clubs with geographic filtering"""
    query = request.GET.get('q', '').strip()
    province_id = request.GET.get('province_id')
    region_id = request.GET.get('region_id')
    lfa_id = request.GET.get('lfa_id')
    
    if len(query) < 2:
        return Response({'results': []})
    
    clubs_qs = Club.objects.filter(
        name__icontains=query,
        is_active=True
    ).select_related('province', 'region', 'lfa')
    
    # Apply geographic filters
    if lfa_id:
        clubs_qs = clubs_qs.filter(lfa_id=lfa_id)
    elif region_id:
        clubs_qs = clubs_qs.filter(region_id=region_id)
    elif province_id:
        clubs_qs = clubs_qs.filter(province_id=province_id)
    
    clubs = clubs_qs[:10]
    
    results = []
    for club in clubs:
        location_parts = []
        if club.lfa:
            location_parts.append(club.lfa.name)
        if club.region:
            location_parts.append(club.region.name)
        if club.province:
            location_parts.append(club.province.name)
        
        results.append({
            'id': club.id,
            'name': club.name,
            'short_name': getattr(club, 'short_name', ''),
            'location': ' - '.join(location_parts) if location_parts else 'Unknown Location',
            'member_count': club.current_members.filter(status='ACTIVE').count()
        })
    
    return Response({'results': results})


class MemberRegistrationAPIView(generics.CreateAPIView):
    """API endpoint for member registration"""
    serializer_class = MemberRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    member = serializer.save()
                    
                    # Create invoice
                    invoice = Invoice.create_member_invoice(
                        member, 
                        member.current_season
                    )
                    
                    # Send confirmation email
                    self.send_registration_email(member, invoice)
                    
                    return Response({
                        'success': True,
                        'message': 'Registration completed successfully',
                        'data': {
                            'member_id': member.id,
                            'safa_id': member.safa_id,
                            'invoice_number': invoice.invoice_number,
                            'amount_due': float(invoice.total_amount)
                        }
                    }, status=status.HTTP_201_CREATED)
                    
            except ValidationError as e:
                return Response({
                    'success': False,
                    'message': str(e),
                    'errors': {'non_field_errors': [str(e)]}
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Member registration error: {e}")
                return Response({
                    'success': False,
                    'message': 'Registration failed due to system error',
                    'errors': {'non_field_errors': ['System error occurred']}
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': False,
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def send_registration_email(self, member, invoice):
        """Send registration confirmation email"""
        try:
            subject = f'SAFA Registration Confirmation - {member.safa_id}'
            message = f"""
Dear {member.get_full_name()},

Your SAFA registration has been submitted successfully.

Registration Details:
- SAFA ID: {member.safa_id}
- Club: {member.current_club.name if member.current_club else 'N/A'}
- Season: {member.current_season.season_year if member.current_season else 'N/A'}

Payment Information:
- Invoice Number: {invoice.invoice_number}
- Amount Due: R{invoice.total_amount}
- Due Date: {invoice.due_date}

Please complete payment to activate your membership.

Thank you,
SAFA Registration Team
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email='noreply@safa.org.za',
                recipient_list=[member.email],
                fail_silently=True
            )
        except Exception as e:
            logger.warning(f"Failed to send registration email to {member.email}: {e}")


# ============================================================================
# TRANSFER API ENDPOINTS
# ============================================================================

class TransferListAPIView(generics.ListCreateAPIView):
    """List and create transfers"""
    serializer_class = TransferSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        qs = Transfer.objects.select_related(
            'member', 'from_club', 'to_club', 'approved_by'
        ).order_by('-request_date')
        
        # Filter based on user permissions
        user = self.request.user
        if not (user.is_superuser or user.is_staff):
            try:
                member_profile = user.member_profile
                if hasattr(member_profile, 'current_club') and member_profile.current_club:
                    qs = qs.filter(
                        Q(from_club=member_profile.current_club) | 
                        Q(to_club=member_profile.current_club) |
                        Q(member=member_profile)
                    )
                else:
                    return Transfer.objects.none()
            except AttributeError:
                return Transfer.objects.none()
        
        return qs


class TransferDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Transfer detail, update, and delete"""
    serializer_class = TransferSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Transfer.objects.select_related(
            'member', 'from_club', 'to_club', 'approved_by'
        )


class TransferApprovalAPIView(APIView):
    """Approve or reject transfer requests"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can approve transfers'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        transfer = get_object_or_404(Transfer, pk=pk)
        action = request.data.get('action')
        reason = request.data.get('reason', '')
        
        if action == 'approve':
            try:
                transfer.approve(request.user)
                return Response({
                    'success': True,
                    'message': 'Transfer approved successfully'
                })
            except ValidationError as e:
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        elif action == 'reject':
            if not reason:
                return Response({
                    'success': False,
                    'message': 'Rejection reason is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                transfer.reject(request.user, reason)
                return Response({
                    'success': True,
                    'message': 'Transfer rejected successfully'
                })
            except ValidationError as e:
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        else:
            return Response({
                'success': False,
                'message': 'Invalid action. Use "approve" or "reject"'
            }, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# DRF VIEWSETS FOR ROUTER
# ============================================================================

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly


class MemberViewSet(viewsets.ModelViewSet):
    """ViewSet for Member CRUD operations"""
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Apply permissions and filtering"""
        qs = Member.objects.select_related(
            'current_club', 'current_season', 'province', 'region', 'lfa', 'user'
        ).prefetch_related('associations', 'documents')
        
        # Apply user permissions
        user = self.request.user
        if not (user.is_superuser or user.is_staff):
            try:
                member_profile = user.member_profile
                if hasattr(member_profile, 'current_club') and member_profile.current_club:
                    qs = qs.filter(current_club=member_profile.current_club)
                else:
                    return Member.objects.none()
            except AttributeError:
                return Member.objects.none()
        
        # Apply query filters
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        
        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)
        
        club_id = self.request.query_params.get('club')
        if club_id:
            qs = qs.filter(current_club_id=club_id)
        
        season_id = self.request.query_params.get('season')
        if season_id:
            qs = qs.filter(current_season_id=season_id)
        
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(safa_id__icontains=search)
            )
        
        return qs.order_by('-created')
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'list':
            return MemberSummarySerializer
        elif self.action == 'create':
            return MemberRegistrationSerializer
        return MemberSerializer
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        """Approve a member's SAFA registration"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can approve members'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        member = self.get_object()
        if member.status != 'PENDING':
            return Response({
                'success': False,
                'message': 'Only pending members can be approved'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            member.approve_safa_membership(request.user)
            return Response({
                'success': True,
                'message': 'Member approved successfully',
                'data': MemberSerializer(member).data
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        """Reject a member's SAFA registration"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can reject members'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        member = self.get_object()
        reason = request.data.get('reason', '')
        
        if not reason:
            return Response({
                'success': False,
                'message': 'Rejection reason is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if member.status != 'PENDING':
            return Response({
                'success': False,
                'message': 'Only pending members can be rejected'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            member.reject_safa_membership(request.user, reason)
            return Response({
                'success': True,
                'message': 'Member rejected successfully',
                'data': MemberSerializer(member).data
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def history(self, request, pk=None):
        """Get member's season history"""
        member = self.get_object()
        history = member.season_history.all().order_by('-season_config__season_year')
        
        from .serializers import MemberSeasonHistorySerializer
        serializer = MemberSeasonHistorySerializer(history, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def documents(self, request, pk=None):
        """Get member's documents"""
        member = self.get_object()
        documents = member.documents.all().order_by('-created')
        
        serializer = MemberDocumentSerializer(documents, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def create_invoice(self, request, pk=None):
        """Create invoice for member"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can create invoices'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        member = self.get_object()
        season_id = request.data.get('season_id')
        
        try:
            if season_id:
                season = SAFASeasonConfig.objects.get(pk=season_id)
            else:
                season = member.current_season or SAFASeasonConfig.get_active_season()
            
            if not season:
                return Response({
                    'success': False,
                    'message': 'No season specified or active'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if invoice already exists
            existing_invoice = Invoice.objects.filter(
                member=member,
                season_config=season,
                status__in=['PENDING', 'PARTIALLY_PAID']
            ).first()
            
            if existing_invoice:
                return Response({
                    'success': False,
                    'message': 'Member already has a pending invoice for this season'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            invoice = Invoice.create_member_invoice(member, season)
            
            return Response({
                'success': True,
                'message': 'Invoice created successfully',
                'data': InvoiceSerializer(invoice).data
            })
            
        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error creating invoice: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InvoiceViewSet(viewsets.ModelViewSet):
    """ViewSet for Invoice CRUD operations"""
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    lookup_field = 'uuid'
    
    def get_queryset(self):
        """Apply permissions and filtering"""
        qs = Invoice.objects.select_related(
            'member', 'season_config', 'content_type', 'issued_by'
        ).prefetch_related('items')
        
        # Apply user permissions
        user = self.request.user
        if not (user.is_superuser or user.is_staff):
            try:
                member_profile = user.member_profile
                qs = qs.filter(member=member_profile)
            except AttributeError:
                return Invoice.objects.none()
        
        # Apply filters
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        
        invoice_type = self.request.query_params.get('type')
        if invoice_type:
            qs = qs.filter(invoice_type=invoice_type)
        
        season_id = self.request.query_params.get('season')
        if season_id:
            qs = qs.filter(season_config_id=season_id)
        
        member_id = self.request.query_params.get('member')
        if member_id:
            qs = qs.filter(member_id=member_id)
        
        # Date range filtering
        date_from = self.request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(issue_date__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(issue_date__lte=date_to)
        
        return qs.order_by('-created')
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_paid(self, request, uuid=None):
        """Mark invoice as paid"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can mark invoices as paid'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        invoice = self.get_object()
        payment_method = request.data.get('payment_method', 'MANUAL')
        payment_reference = request.data.get('payment_reference', '')
        
        if invoice.status == 'PAID':
            return Response({
                'success': False,
                'message': 'Invoice is already paid'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            invoice.mark_as_paid(
                payment_method=payment_method,
                payment_reference=payment_reference
            )
            
            return Response({
                'success': True,
                'message': 'Invoice marked as paid successfully',
                'data': InvoiceSerializer(invoice).data
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def process_payment(self, request, uuid=None):
        """Process partial or full payment"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can process payments'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        invoice = self.get_object()
        serializer = InvoicePaymentSerializer(data=request.data, instance=invoice)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    payment_data = serializer.validated_data
                    
                    # Update invoice payment
                    invoice.paid_amount += payment_data['amount']
                    invoice.payment_method = payment_data['payment_method']
                    invoice.payment_reference = payment_data.get('payment_reference', '')
                    
                    if invoice.paid_amount >= invoice.total_amount:
                        invoice.mark_as_paid(
                            payment_method=payment_data['payment_method'],
                            payment_reference=payment_data.get('payment_reference', '')
                        )
                    else:
                        invoice.status = 'PARTIALLY_PAID'
                        invoice.save()
                    
                    return Response({
                        'success': True,
                        'message': 'Payment processed successfully',
                        'data': InvoiceSerializer(invoice).data
                    })
                    
            except Exception as e:
                return Response({
                    'success': False,
                    'message': f'Payment processing failed: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def send_reminder(self, request, uuid=None):
        """Send payment reminder email"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can send reminders'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        invoice = self.get_object()
        
        if invoice.status not in ['PENDING', 'OVERDUE', 'PARTIALLY_PAID']:
            return Response({
                'success': False,
                'message': 'Payment reminder can only be sent for unpaid invoices'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            recipient_email = None
            recipient_name = None
            
            if invoice.member:
                recipient_email = invoice.member.email
                recipient_name = invoice.member.get_full_name()
            elif invoice.organization:
                recipient_name = getattr(invoice.organization, 'name', str(invoice.organization))
                # Try to find admin email for organizations
                # This would need to be implemented based on your organization structure
            
            if recipient_email and recipient_name:
                subject = f'Payment Reminder - Invoice #{invoice.invoice_number}'
                message = f"""
Dear {recipient_name},

This is a reminder that your invoice #{invoice.invoice_number} for R{invoice.total_amount:.2f} is outstanding.

Invoice Details:
- Amount Due: R{invoice.outstanding_amount:.2f}
- Due Date: {invoice.due_date}
- Status: {invoice.get_status_display()}

Please log in to the SAFA system to view and pay this invoice.

Thank you,
SAFA Finance Team
                """
                
                success = send_mail(
                    subject=subject,
                    message=message,
                    from_email='finance@safa.org.za',
                    recipient_list=[recipient_email],
                    fail_silently=False
                )
                
                if success:
                    return Response({
                        'success': True,
                        'message': f'Payment reminder sent to {recipient_name}'
                    })
                else:
                    return Response({
                        'success': False,
                        'message': 'Failed to send payment reminder'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({
                    'success': False,
                    'message': 'No valid email address found for this invoice'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error sending reminder: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def overdue(self, request):
        """Get overdue invoices"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can view overdue invoices'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        overdue_invoices = self.get_queryset().filter(
            status__in=['PENDING', 'PARTIALLY_PAID'],
            due_date__lt=timezone.now().date()
        )
        
        page = self.paginate_queryset(overdue_invoices)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(overdue_invoices, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })


class TransferViewSet(viewsets.ModelViewSet):
    """ViewSet for Transfer CRUD operations"""
    serializer_class = TransferSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Apply permissions and filtering"""
        qs = Transfer.objects.select_related(
            'member', 'from_club', 'to_club', 'approved_by'
        )
        
        # Apply user permissions
        user = self.request.user
        if not (user.is_superuser or user.is_staff):
            try:
                member_profile = user.member_profile
                if hasattr(member_profile, 'current_club') and member_profile.current_club:
                    # Users can see transfers involving their club or their own transfers
                    qs = qs.filter(
                        Q(from_club=member_profile.current_club) | 
                        Q(to_club=member_profile.current_club) |
                        Q(member=member_profile)
                    )
                else:
                    return Transfer.objects.none()
            except AttributeError:
                return Transfer.objects.none()
        
        # Apply filters
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        
        member_id = self.request.query_params.get('member')
        if member_id:
            qs = qs.filter(member_id=member_id)
        
        from_club_id = self.request.query_params.get('from_club')
        if from_club_id:
            qs = qs.filter(from_club_id=from_club_id)
        
        to_club_id = self.request.query_params.get('to_club')
        if to_club_id:
            qs = qs.filter(to_club_id=to_club_id)
        
        return qs.order_by('-request_date')
    
    def perform_create(self, serializer):
        """Set from_club when creating transfer"""
        member = serializer.validated_data['member']
        serializer.save(from_club=member.current_club)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        """Approve a transfer request"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can approve transfers'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        transfer = self.get_object()
        
        if transfer.status != 'PENDING':
            return Response({
                'success': False,
                'message': 'Only pending transfers can be approved'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            transfer.approve(request.user)
            return Response({
                'success': True,
                'message': 'Transfer approved successfully',
                'data': TransferSerializer(transfer).data
            })
        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        """Reject a transfer request"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can reject transfers'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        transfer = self.get_object()
        reason = request.data.get('reason', '')
        
        if not reason:
            return Response({
                'success': False,
                'message': 'Rejection reason is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if transfer.status != 'PENDING':
            return Response({
                'success': False,
                'message': 'Only pending transfers can be rejected'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            transfer.reject(request.user, reason)
            return Response({
                'success': True,
                'message': 'Transfer rejected successfully',
                'data': TransferSerializer(transfer).data
            })
        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def pending(self, request):
        """Get pending transfers"""
        pending_transfers = self.get_queryset().filter(status='PENDING')
        
        page = self.paginate_queryset(pending_transfers)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(pending_transfers, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })


class SeasonConfigViewSet(viewsets.ModelViewSet):
    """ViewSet for SAFASeasonConfig CRUD operations"""
    serializer_class = SAFASeasonConfigSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return SAFASeasonConfig.objects.all().order_by('-season_year')
    
    def get_permissions(self):
        """Only staff can create/update/delete seasons"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
            # Additional check in the view method
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def create(self, request, *args, **kwargs):
        """Create new season configuration"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can create seasons'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Update season configuration"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can update seasons'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete season configuration"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can delete seasons'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        """Set created_by when creating season"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def activate(self, request, pk=None):
        """Activate a season configuration"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can activate seasons'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        season = self.get_object()
        
        try:
            with transaction.atomic():
                # Deactivate all other seasons
                SAFASeasonConfig.objects.exclude(pk=season.pk).update(is_active=False)
                
                # Activate this season
                season.is_active = True
                season.save()
                
                return Response({
                    'success': True,
                    'message': f'Season {season.season_year} activated successfully',
                    'data': SAFASeasonConfigSerializer(season).data
                })
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error activating season: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def active(self, request):
        """Get the active season"""
        active_season = SAFASeasonConfig.get_active_season()
        
        if active_season:
            serializer = SAFASeasonConfigSerializer(active_season)
            return Response({
                'success': True,
                'data': serializer.data
            })
        else:
            return Response({
                'success': False,
                'message': 'No active season found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def statistics(self, request, pk=None):
        """Get statistics for a season"""
        season = self.get_object()
        
        # Member statistics
        members_qs = Member.objects.filter(current_season=season)
        
        stats = {
            'season_year': season.season_year,
            'is_active': season.is_active,
            'member_statistics': {
                'total_members': members_qs.count(),
                'active_members': members_qs.filter(status='ACTIVE').count(),
                'pending_members': members_qs.filter(status='PENDING').count(),
                'players': members_qs.filter(role='PLAYER').count(),
                'officials': members_qs.filter(role='OFFICIAL').count(),
            },
            'financial_statistics': {
                'total_invoices': season.invoices.count(),
                'paid_invoices': season.invoices.filter(status='PAID').count(),
                'pending_invoices': season.invoices.filter(status='PENDING').count(),
                'total_revenue': float(season.invoices.filter(status='PAID').aggregate(
                    total=Sum('total_amount')
                )['total'] or 0),
                'outstanding_revenue': float(season.invoices.filter(
                    status__in=['PENDING', 'OVERDUE', 'PARTIALLY_PAID']
                ).aggregate(
                    total=Sum('outstanding_amount')
                )['total'] or 0),
            },
            'registration_periods': {
                'organization_registration_open': season.organization_registration_open,
                'member_registration_open': season.member_registration_open,
            }
        }
        
        return Response({
            'success': True,
            'data': stats
        })
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def fee_structures(self, request, pk=None):
        """Get fee structures for a season"""
        season = self.get_object()
        fee_structures = season.fee_structures.all().order_by('entity_type')
        
        from .serializers import SAFAFeeStructureSerializer
        serializer = SAFAFeeStructureSerializer(fee_structures, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Invalid action. Use "approve" or "reject"'
        },  status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# INVOICE API ENDPOINTS
# ============================================================================

class InvoiceListAPIView(generics.ListAPIView):
    """List invoices with filtering"""
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        qs = Invoice.objects.select_related(
            'member', 'season_config', 'content_type'
        ).prefetch_related('items').order_by('-created')
        
        # Apply user permissions
        user = self.request.user
        if not (user.is_superuser or user.is_staff):
            try:
                member_profile = user.member_profile
                qs = qs.filter(member=member_profile)
            except AttributeError:
                return Invoice.objects.none()
        
        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        
        invoice_type = self.request.query_params.get('type')
        if invoice_type:
            qs = qs.filter(invoice_type=invoice_type)
        
        season_id = self.request.query_params.get('season')
        if season_id:
            qs = qs.filter(season_config_id=season_id)
        
        return qs


class InvoiceDetailAPIView(generics.RetrieveAPIView):
    """Invoice detail"""
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'uuid'
    
    def get_queryset(self):
        qs = Invoice.objects.select_related(
            'member', 'season_config', 'content_type'
        ).prefetch_related('items')
        
        user = self.request.user
        if not (user.is_superuser or user.is_staff):
            try:
                member_profile = user.member_profile
                qs = qs.filter(member=member_profile)
            except AttributeError:
                return Invoice.objects.none()
        
        return qs


class InvoicePaymentAPIView(APIView):
    """Process invoice payments"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, uuid):
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can process payments'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        invoice = get_object_or_404(Invoice, uuid=uuid)
        
        serializer = InvoicePaymentSerializer(data=request.data, instance=invoice)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    payment_data = serializer.validated_data
                    
                    # Update invoice payment
                    invoice.paid_amount += payment_data['amount']
                    invoice.payment_method = payment_data['payment_method']
                    invoice.payment_reference = payment_data.get('payment_reference', '')
                    
                    if invoice.paid_amount >= invoice.total_amount:
                        invoice.mark_as_paid(
                            payment_method=payment_data['payment_method'],
                            payment_reference=payment_data.get('payment_reference', '')
                        )
                    else:
                        invoice.status = 'PARTIALLY_PAID'
                        invoice.save()
                    
                    return Response({
                        'success': True,
                        'message': 'Payment processed successfully',
                        'data': {
                            'paid_amount': float(invoice.paid_amount),
                            'outstanding_amount': float(invoice.outstanding_amount),
                            'status': invoice.status
                        }
                    })
                    
            except Exception as e:
                return Response({
                    'success': False,
                    'message': f'Payment processing failed: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# WORKFLOW API ENDPOINTS
# ============================================================================

class WorkflowListAPIView(generics.ListAPIView):
    """List registration workflows"""
    serializer_class = RegistrationWorkflowSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        qs = RegistrationWorkflow.objects.select_related(
            'member', 'member__current_club'
        ).order_by('completion_percentage', '-created')
        
        # Filter incomplete workflows
        incomplete_only = self.request.query_params.get('incomplete_only', 'true')
        if incomplete_only.lower() == 'true':
            qs = qs.exclude(current_step='COMPLETE')
        
        return qs


class WorkflowDetailAPIView(generics.RetrieveUpdateAPIView):
    """Workflow detail and update"""
    serializer_class = RegistrationWorkflowSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return RegistrationWorkflow.objects.select_related(
            'member', 'member__current_club'
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def workflow_progress(request):
    """Get workflow progress statistics"""
    total_workflows = RegistrationWorkflow.objects.count()
    
    if total_workflows == 0:
        return Response({
            'total_workflows': 0,
            'completion_stats': {},
            'step_stats': {}
        })
    
    # Completion statistics
    completion_ranges = [
        (0, 20, 'Not Started'),
        (21, 40, 'Getting Started'),
        (41, 60, 'In Progress'),
        (61, 80, 'Nearly Complete'),
        (81, 100, 'Complete')
    ]
    
    completion_stats = {}
    for min_pct, max_pct, label in completion_ranges:
        count = RegistrationWorkflow.objects.filter(
            completion_percentage__gte=min_pct,
            completion_percentage__lte=max_pct
        ).count()
        completion_stats[label] = {
            'count': count,
            'percentage': round((count / total_workflows) * 100, 1)
        }
    
    # Step statistics
    step_stats = {}
    for step, label in RegistrationWorkflow.WORKFLOW_STEPS:
        count = RegistrationWorkflow.objects.filter(current_step=step).count()
        step_stats[label] = {
            'count': count,
            'percentage': round((count / total_workflows) * 100, 1)
        }
    
    return Response({
        'total_workflows': total_workflows,
        'completion_stats': completion_stats,
        'step_stats': step_stats
    })


# ============================================================================
# DOCUMENT API ENDPOINTS
# ============================================================================

class DocumentListAPIView(generics.ListAPIView):
    """List member documents"""
    serializer_class = MemberDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        qs = MemberDocument.objects.select_related(
            'member', 'verified_by'
        ).order_by('-created')
        
        # Filter by verification status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(verification_status=status_filter)
        
        # Filter by member
        member_id = self.request.query_params.get('member_id')
        if member_id:
            qs = qs.filter(member_id=member_id)
        
        return qs


class DocumentUploadAPIView(generics.CreateAPIView):
    """Upload member documents"""
    serializer_class = MemberDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        member_id = request.data.get('member_id')
        if not member_id:
            return Response({
                'success': False,
                'message': 'Member ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            member = Member.objects.get(pk=member_id)
        except Member.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Member not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            document = serializer.save(member=member)
            
            return Response({
                'success': True,
                'message': 'Document uploaded successfully',
                'data': MemberDocumentSerializer(document).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class DocumentApprovalAPIView(APIView):
    """Approve or reject documents"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can approve documents'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        document = get_object_or_404(MemberDocument, pk=pk)
        action = request.data.get('action')
        notes = request.data.get('notes', '')
        
        if action == 'approve':
            document.approve(request.user)
            return Response({
                'success': True,
                'message': 'Document approved successfully'
            })
        
        elif action == 'reject':
            if not notes:
                return Response({
                    'success': False,
                    'message': 'Notes are required for rejection'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            document.reject(request.user, notes)
            return Response({
                'success': True,
                'message': 'Document rejected successfully'
            })
        
        else:
            return Response({
                'success': False,
                'message': 'Try again next time'

            })
                