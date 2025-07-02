"""
SAFA Digital Card Views
Views for displaying, downloading, and managing digital membership cards
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.http import require_GET, require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.conf import settings

from membership.models import Member
from .card_generator import SAFACardGenerator
import os


@login_required
def my_digital_card(request):
    """Display user's digital membership card"""
    try:
        # Get the member associated with the current user
        member = Member.objects.get(email=request.user.email)
        
        if not member.safa_id:
            messages.warning(request, "Your SAFA ID has not been assigned yet. Please contact an administrator.")
            return render(request, 'membership_cards/no_card.html')
        
        context = {
            'member': member,
            'card_ready': True,
        }
        return render(request, 'membership_cards/my_card.html', context)
        
    except Member.DoesNotExist:
        messages.error(request, "No membership record found for your account.")
        return render(request, 'membership_cards/no_card.html')


@login_required
def download_my_card(request, format_type='mobile'):
    """Download user's membership card in specified format"""
    try:
        member = Member.objects.get(email=request.user.email)
        
        if not member.safa_id:
            messages.error(request, "Your SAFA ID has not been assigned yet.")
            return redirect('membership_cards:my_card')
        
        generator = SAFACardGenerator()
        
        if format_type == 'mobile':
            card_data = generator.generate_mobile_card(member)
            response = HttpResponse(card_data.read(), content_type='image/png')
            response['Content-Disposition'] = f'attachment; filename="SAFA_Card_{member.safa_id}_Mobile.png"'
            
        elif format_type == 'print':
            card_data = generator.generate_print_card_pdf(member)
            response = HttpResponse(card_data.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="SAFA_Card_{member.safa_id}_Print.pdf"'
            
        elif format_type == 'digital':
            card_image = generator.generate_card_image(member)
            import io
            img_io = io.BytesIO()
            card_image.save(img_io, format='PNG', dpi=(300, 300))
            img_io.seek(0)
            
            response = HttpResponse(img_io.read(), content_type='image/png')
            response['Content-Disposition'] = f'attachment; filename="SAFA_Card_{member.safa_id}_Digital.png"'
            
        else:
            messages.error(request, "Invalid card format requested.")
            return redirect('membership_cards:my_card')
        
        return response
        
    except Member.DoesNotExist:
        messages.error(request, "No membership record found.")
        return redirect('membership_cards:my_card')
    except Exception as e:
        messages.error(request, f"Error generating card: {str(e)}")
        return redirect('membership_cards:my_card')


@login_required
def card_preview_image(request):
    """Return card image for preview (AJAX endpoint)"""
    try:
        member = Member.objects.get(email=request.user.email)
        
        if not member.safa_id:
            return JsonResponse({'error': 'SAFA ID not assigned'}, status=400)
        
        generator = SAFACardGenerator()
        card_data = generator.generate_mobile_card(member)
        
        response = HttpResponse(card_data.read(), content_type='image/png')
        response['Cache-Control'] = 'max-age=300'  # Cache for 5 minutes
        return response
        
    except Member.DoesNotExist:
        return JsonResponse({'error': 'Member not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def admin_card_management(request):
    """Admin view for managing member cards"""
    search_query = request.GET.get('search', '')
    
    members = Member.objects.all()
    
    if search_query:
        members = members.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(safa_id__icontains=search_query)
        )
    
    # Separate members with and without SAFA IDs
    members_with_ids = members.filter(safa_id__isnull=False).order_by('last_name', 'first_name')
    members_without_ids = members.filter(safa_id__isnull=True).order_by('last_name', 'first_name')
    
    # Pagination
    paginator_with_ids = Paginator(members_with_ids, 25)
    paginator_without_ids = Paginator(members_without_ids, 25)
    
    page_with_ids = request.GET.get('page_with_ids', 1)
    page_without_ids = request.GET.get('page_without_ids', 1)
    
    members_with_ids_page = paginator_with_ids.get_page(page_with_ids)
    members_without_ids_page = paginator_without_ids.get_page(page_without_ids)
    
    context = {
        'members_with_ids': members_with_ids_page,
        'members_without_ids': members_without_ids_page,
        'search_query': search_query,
        'total_with_ids': members_with_ids.count(),
        'total_without_ids': members_without_ids.count(),
    }
    
    return render(request, 'membership_cards/admin_management.html', context)


@staff_member_required
def admin_generate_card(request, member_id):
    """Generate card for a specific member (admin only)"""
    member = get_object_or_404(Member, id=member_id)
    
    if not member.safa_id:
        messages.error(request, f"Cannot generate card for {member.get_full_name()}: SAFA ID not assigned.")
        return redirect('membership_cards:admin_management')
    
    format_type = request.GET.get('format', 'mobile')
    
    try:
        generator = SAFACardGenerator()
        
        if format_type == 'mobile':
            card_data = generator.generate_mobile_card(member)
            response = HttpResponse(card_data.read(), content_type='image/png')
            response['Content-Disposition'] = f'attachment; filename="SAFA_Card_{member.safa_id}_Mobile.png"'
            
        elif format_type == 'print':
            card_data = generator.generate_print_card_pdf(member)
            response = HttpResponse(card_data.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="SAFA_Card_{member.safa_id}_Print.pdf"'
            
        elif format_type == 'digital':
            card_image = generator.generate_card_image(member)
            import io
            img_io = io.BytesIO()
            card_image.save(img_io, format='PNG', dpi=(300, 300))
            img_io.seek(0)
            
            response = HttpResponse(img_io.read(), content_type='image/png')
            response['Content-Disposition'] = f'attachment; filename="SAFA_Card_{member.safa_id}_Digital.png"'
            
        else:
            messages.error(request, "Invalid card format requested.")
            return redirect('membership_cards:admin_management')
        
        return response
        
    except Exception as e:
        messages.error(request, f"Error generating card for {member.get_full_name()}: {str(e)}")
        return redirect('membership_cards:admin_management')


@staff_member_required
@require_POST
def admin_bulk_generate_cards(request):
    """Generate cards for multiple members (admin only)"""
    member_ids = request.POST.getlist('member_ids')
    format_type = request.POST.get('format', 'mobile')
    
    if not member_ids:
        messages.error(request, "No members selected.")
        return redirect('membership_cards:admin_management')
    
    members = Member.objects.filter(id__in=member_ids, safa_id__isnull=False)
    
    if not members.exists():
        messages.error(request, "No valid members selected (members must have SAFA IDs).")
        return redirect('membership_cards:admin_management')
    
    try:
        generator = SAFACardGenerator()
        results = generator.bulk_generate_cards(members, format_type)
        
        success_count = sum(1 for r in results if r['success'])
        error_count = len(results) - success_count
        
        if success_count > 0:
            messages.success(request, f"Successfully generated {success_count} card(s).")
        
        if error_count > 0:
            messages.warning(request, f"Failed to generate {error_count} card(s).")
            
        return redirect('membership_cards:admin_management')
        
    except Exception as e:
        messages.error(request, f"Error during bulk generation: {str(e)}")
        return redirect('membership_cards:admin_management')


@staff_member_required
def admin_card_preview(request, member_id):
    """Preview card for a specific member (admin only)"""
    member = get_object_or_404(Member, id=member_id)
    
    if not member.safa_id:
        return JsonResponse({'error': 'SAFA ID not assigned'}, status=400)
    
    try:
        generator = SAFACardGenerator()
        card_data = generator.generate_mobile_card(member)
        
        response = HttpResponse(card_data.read(), content_type='image/png')
        response['Cache-Control'] = 'max-age=300'  # Cache for 5 minutes
        return response
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def card_verification(request, safa_id):
    """Public endpoint for verifying card authenticity via QR code"""
    try:
        member = Member.objects.get(safa_id=safa_id)
        
        # Basic verification info (no sensitive data)
        verification_data = {
            'valid': True,
            'name': member.get_full_name(),
            'safa_id': member.safa_id,
            'status': member.status,
            'verified_at': timezone.now().isoformat(),
        }
        
        return JsonResponse(verification_data)
        
    except Member.DoesNotExist:
        return JsonResponse({
            'valid': False,
            'error': 'Member not found',
            'verified_at': timezone.now().isoformat(),
        }, status=404)
