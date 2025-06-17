from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import get_user_model
from django.core import signing
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
import base64
import json
import os

from .models import DigitalCard, PhysicalCard
from .google_wallet import GoogleWalletManager
from rest_framework import viewsets
from .serializers import DigitalCardSerializer

User = get_user_model()

@login_required
def my_digital_card(request):
    """Display user's digital membership card"""
    try:
        digital_card = request.user.digital_card
        context = {
            'card': digital_card,
            'user': request.user,
            'qr_base64': digital_card.get_qr_base64(),
        }
        return render(request, 'membership_cards/digital_card.html', context)
    except DigitalCard.DoesNotExist:
        return render(request, 'membership_cards/no_card.html')

@login_required
def card_qr_code(request):
    """Return QR code as JSON for PWA/offline use"""
    try:
        digital_card = request.user.digital_card
        return JsonResponse({
            'qr_data': digital_card.qr_code_data,
            'qr_image': digital_card.get_qr_base64(),
            'status': digital_card.status,
            'expires': digital_card.expires_date.isoformat(),
            'valid': digital_card.is_valid()
        })
    except DigitalCard.DoesNotExist:
        return JsonResponse({'error': 'No digital card found'}, status=404)

def verify_qr_code(request):
    """Verify scanned QR code (public endpoint for scanners)"""
    if request.method == 'POST':
        try:
            qr_data = request.POST.get('qr_data', '').strip()
            if not qr_data:
                return JsonResponse({'error': 'No QR data provided'}, status=400)
            
            # Try to decode the signed data
            try:
                decoded_data = signing.loads(qr_data)
            except signing.BadSignature:
                # If direct decoding fails, try base64 decoding first
                try:
                    import base64
                    decoded_qr = base64.b64decode(qr_data).decode()
                    decoded_data = signing.loads(decoded_qr)
                except:
                    return JsonResponse({
                        'valid': False,
                        'error': 'Invalid QR code format',
                        'debug_info': f'Raw data length: {len(qr_data)} characters'
                    }, status=400)
            
            # Get user and card information
            user_id = decoded_data.get('u')
            if not user_id:
                return JsonResponse({
                    'valid': False,
                    'error': 'Invalid QR code - missing user ID'
                }, status=400)
            
            try:
                user = User.objects.get(id=user_id)
                digital_card = user.digital_card
            except (User.DoesNotExist, DigitalCard.DoesNotExist):
                return JsonResponse({
                    'valid': False,
                    'error': 'User or card not found'
                }, status=400)
            
            # Verify card is still valid
            if not digital_card.is_valid():
                return JsonResponse({
                    'valid': False,
                    'reason': f'Card {digital_card.status.lower()}'
                })
            
            return JsonResponse({
                'valid': True,
                'name': f"{user.name} {user.surname}",
                'safa_id': user.safa_id,
                'card_number': digital_card.card_number,
                'expires': digital_card.expires_date.isoformat(),
                'status': digital_card.status,
                'card_type': 'Digital'
            })
            
        except Exception as e:
            return JsonResponse({
                'valid': False,
                'error': 'QR code verification failed',
                'debug_info': str(e)
            }, status=400)
    
    return render(request, 'membership_cards/qr_scanner.html')

@login_required
def download_card(request):
    """Download card as image for sharing"""
    try:
        digital_card = request.user.digital_card
        if digital_card.qr_image:
            response = HttpResponse(
                digital_card.qr_image.read(),
                content_type='image/png'
            )
            response['Content-Disposition'] = f'attachment; filename="safa_card_{digital_card.card_number}.png"'
            return response
    except DigitalCard.DoesNotExist:
        pass
    
    return HttpResponse('Card not found', status=404)

@login_required
def test_card_generation(request):
    """Test endpoint to manually generate a card for testing"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Staff only'}, status=403)
    
    try:
        # Ensure user has required fields
        if not request.user.safa_id:
            request.user.generate_safa_id()
            request.user.save()
        
        # Create or get digital card
        digital_card, created = DigitalCard.objects.get_or_create(
            user=request.user,
            defaults={
                'expires_date': timezone.now().date() + timezone.timedelta(days=365),
                'status': 'ACTIVE'
            }
        )
        
        return JsonResponse({
            'success': True,
            'created': created,
            'card_number': digital_card.card_number,
            'has_qr_image': bool(digital_card.qr_image),
            'redirect_url': '/cards/my-card/'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required  
def debug_qr_data(request):
    """Debug view to show QR code contents"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Staff only'}, status=403)
        
    try:
        digital_card = request.user.digital_card
        
        # Show both the raw data and decoded data
        raw_data = digital_card.qr_code_data
        
        try:
            decoded_data = signing.loads(raw_data)
        except:
            decoded_data = "Failed to decode"
            
        return JsonResponse({
            'raw_qr_data': raw_data,
            'raw_length': len(raw_data),
            'decoded_data': decoded_data,
            'card_number': digital_card.card_number,
            'user_info': {
                'id': request.user.id,
                'name': f"{request.user.name} {request.user.surname}",
                'safa_id': request.user.safa_id
            }
        })
        
    except DigitalCard.DoesNotExist:
        return JsonResponse({'error': 'No digital card found'})

@login_required  
def test_qr_decode(request):
    """Test view to decode the QR code from your scan"""
    if request.method == 'POST':
        qr_input = request.POST.get('qr_data', '').strip()
        
        results = {
            'raw_input': qr_input,
            'input_length': len(qr_input),
            'is_numeric': qr_input.isdigit(),
        }
        
        # Test 1: Try as Django signed data
        try:
            decoded = signing.loads(qr_input)
            results['django_decode'] = decoded
            results['django_success'] = True
        except:
            results['django_success'] = False
            results['django_error'] = 'Not Django signed data'
        
        # Test 2: Check if it's just a card number
        if qr_input.isdigit():
            try:
                card = DigitalCard.objects.get(card_number=qr_input)
                results['card_lookup'] = {
                    'found': True,
                    'user': card.user.get_full_name(),
                    'safa_id': card.user.safa_id,
                    'status': card.status
                }
            except DigitalCard.DoesNotExist:
                results['card_lookup'] = {'found': False}
        
        return JsonResponse(results)
    
    return render(request, 'membership_cards/test_qr.html')

@login_required
def force_regenerate_qr(request):
    """Force regenerate QR code for current user"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Staff only'}, status=403)
    
    try:
        digital_card = request.user.digital_card
        
        # Delete old QR image
        if digital_card.qr_image:
            digital_card.qr_image.delete()
        
        # Increment version to force regeneration
        digital_card.qr_code_version += 1
        
        # Regenerate QR data and image
        digital_card.generate_qr_data()
        success = digital_card.generate_qr_image()
        
        # Save the card
        digital_card.save()
        
        return JsonResponse({
            'success': success,
            'card_number': digital_card.card_number,
            'qr_data_length': len(digital_card.qr_code_data),
            'has_qr_image': bool(digital_card.qr_image),
            'message': 'QR code regenerated successfully' if success else 'QR generation failed'
        })
        
    except DigitalCard.DoesNotExist:
        return JsonResponse({'error': 'No digital card found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def system_dashboard(request):
    """System dashboard showing card statistics"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Staff only'}, status=403)
    
    from django.db.models import Count, Q
    from geography.models import Province, Region, LocalFootballAssociation
    
    # Card statistics
    card_stats = {
        'total_digital_cards': DigitalCard.objects.count(),
        'active_cards': DigitalCard.objects.filter(status='ACTIVE').count(),
        'expired_cards': DigitalCard.objects.filter(status='EXPIRED').count(),
        'suspended_cards': DigitalCard.objects.filter(status='SUSPENDED').count(),
        'total_physical_cards': PhysicalCard.objects.count(),
        'pending_print': PhysicalCard.objects.filter(print_status='PENDING').count(),
        'shipped_cards': PhysicalCard.objects.filter(print_status='SHIPPED').count(),
    }
    
    # Geography statistics  
    geo_stats = {
        'total_provinces': Province.objects.filter(is_active=True).count(),
        'total_regions': Region.objects.filter(is_active=True).count(),
        'total_lfas': LocalFootballAssociation.objects.filter(is_active=True).count(),
    }
    
    # User statistics
    user_stats = {
        'total_users': User.objects.count(),
        'active_memberships': User.objects.filter(membership_status='ACTIVE').count(),
        'pending_memberships': User.objects.filter(membership_status='PENDING').count(),
        'users_with_cards': User.objects.filter(digital_card__isnull=False).count(),
    }
    
    context = {
        'card_stats': card_stats,
        'geo_stats': geo_stats,
        'user_stats': user_stats,
    }
    
    return render(request, 'membership_cards/dashboard.html', context)

class DigitalCardViewSet(viewsets.ModelViewSet):
    queryset = DigitalCard.objects.all()
    serializer_class = DigitalCardSerializer

@login_required
def add_to_google_wallet(request):
    """Add user's digital card to Google Wallet"""
    try:
        # Get the user's digital card
        digital_card = request.user.digital_card
        
        # Initialize the Google Wallet manager
        wallet_manager = GoogleWalletManager()
        
        if not wallet_manager.is_configured():
            # If Google Wallet is not configured, show a message
            return render(request, 'membership_cards/wallet_not_configured.html')
        
        # Set issuer ID and class suffix from settings or use defaults
        issuer_id = getattr(settings, 'GOOGLE_WALLET_ISSUER_ID', '3388000000022222228')
        class_suffix = 'SAFAMembershipCard'
        
        # Generate the JWT token for adding to Google Wallet
        jwt_token = wallet_manager.create_jwt_token(issuer_id, class_suffix, digital_card)
        
        if jwt_token:
            # Construct the save URL with the JWT token
            save_url = f"https://pay.google.com/gp/v/save/{jwt_token}"
            
            # Context for the template
            context = {
                'save_url': save_url,
                'card': digital_card,
                'user': request.user
            }
            
            return render(request, 'membership_cards/add_to_google_wallet.html', context)
        else:
            # Failed to create JWT token
            return render(request, 'membership_cards/wallet_error.html', {
                'error': 'Failed to create wallet token'
            })
    
    except DigitalCard.DoesNotExist:
        # User doesn't have a digital card
        return render(request, 'membership_cards/no_card.html')
    
    except Exception as e:
        # Generic error handling
        return render(request, 'membership_cards/wallet_error.html', {
            'error': str(e)
        })
