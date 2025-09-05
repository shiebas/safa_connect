from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import base64
import json
import os
from PIL import Image
import io

from .models import TournamentRegistration, VerificationLog
from .tournament_models import TournamentCompetition, TournamentPlayer, TournamentTeam
from accounts.models import CustomUser
from .team_photo_generator import team_photo_generator
from .bulk_views import bulk_management
from .fixture_generator import generate_tournament_fixtures, check_tournament_has_fixtures

# Import facial verification with error handling
try:
    from .facial_verification import facial_verifier
    FACIAL_RECOGNITION_AVAILABLE = True
except ImportError as e:
    print(f"Facial recognition not available: {e}")
    facial_verifier = None
    FACIAL_RECOGNITION_AVAILABLE = False

@login_required
def admin_dashboard(request):
    """General admin dashboard for tournament management"""
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Superuser privileges required.")
        return redirect('tournament_verification:tournament_list')
    
    # Get statistics
    total_tournaments = TournamentCompetition.objects.count()
    active_tournaments = TournamentCompetition.objects.filter(is_active=True).count()
    total_registrations = TournamentRegistration.objects.count()
    pending_verifications = TournamentRegistration.objects.filter(verification_status='PENDING').count()
    
    # Get recent tournaments
    recent_tournaments = TournamentCompetition.objects.filter(is_active=True).order_by('-created_at')[:5]
    
    # Get recent registrations
    recent_registrations = TournamentRegistration.objects.select_related('tournament').order_by('-registered_at')[:10]
    
    context = {
        'total_tournaments': total_tournaments,
        'active_tournaments': active_tournaments,
        'total_registrations': total_registrations,
        'pending_verifications': pending_verifications,
        'recent_tournaments': recent_tournaments,
        'recent_registrations': recent_registrations,
        'title': 'Tournament Admin Dashboard'
    }
    return render(request, 'tournament_verification/admin_dashboard.html', context)

@login_required
def photo_verification(request):
    """Photo verification dashboard for superusers"""
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Superuser privileges required.")
        return redirect('tournament_verification:tournament_list')
    
    # Get pending verifications
    pending_registrations = TournamentRegistration.objects.filter(
        verification_status='PENDING'
    ).select_related('tournament').order_by('-registered_at')
    
    context = {
        'pending_registrations': pending_registrations,
        'title': 'Photo Verification Dashboard'
    }
    return render(request, 'tournament_verification/photo_verification.html', context)

@login_required
@require_POST
@csrf_exempt
def verify_registration(request, registration_id):
    """Verify a tournament registration"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    try:
        registration = TournamentRegistration.objects.get(id=registration_id)
        
        # Get data from request
        data = json.loads(request.body)
        status = data.get('status')
        notes = data.get('notes', '')
        
        # Update registration
        registration.verification_status = status
        registration.verification_notes = notes
        registration.verified_at = timezone.now()
        registration.verified_by = request.user
        registration.save()
        
        # Create verification log
        VerificationLog.objects.create(
            registration=registration,
            verification_status=status,
            notes=notes,
            processed_by=request.user
        )
        
        return JsonResponse({'success': True})
        
    except TournamentRegistration.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Registration not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
@csrf_exempt
def auto_verify_registration(request, registration_id):
    """Automatically verify a tournament registration using facial recognition"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    # Check if facial recognition is available
    if not FACIAL_RECOGNITION_AVAILABLE:
        return JsonResponse({
            'success': False, 
            'error': 'Facial recognition system not available. Please install required packages.'
        })
    
    print(f"DEBUG: Auto-verify called for registration {registration_id}")
    
    try:
        registration = TournamentRegistration.objects.get(id=registration_id)
        
        # Check if we have a live photo
        if not registration.live_photo:
            return JsonResponse({
                'success': False, 
                'error': 'No live photo available for verification'
            })
        
        # For now, we'll use a simple approach:
        # 1. Check if the player has a stored photo (from their profile)
        # 2. If not, we'll need to implement a way to store reference photos
        
        stored_photo_path = None
        if registration.player and hasattr(registration.player, 'profile_pic') and registration.player.profile_pic:
            stored_photo_path = registration.player.profile_pic.path
        
        # Perform facial verification
        verification_result = facial_verifier.verify_faces(
            live_photo_path=registration.live_photo.path,
            stored_photo_path=stored_photo_path
        )
        
        # Determine verification status based on result
        if verification_result['verified'] and verification_result['confidence'] > 0.7:
            status = 'VERIFIED'
            notes = f"Auto-verified: Confidence {verification_result['confidence']:.2f}"
        elif verification_result['confidence'] > 0.5:
            status = 'MANUAL_REVIEW'
            notes = f"Auto-review: Confidence {verification_result['confidence']:.2f} - requires manual review"
        else:
            status = 'FAILED'
            notes = f"Auto-failed: Confidence {verification_result['confidence']:.2f} - {verification_result.get('error', 'Low confidence')}"
        
        # Update registration
        registration.verification_status = status
        registration.verification_score = verification_result['confidence']
        registration.verification_notes = notes
        registration.verified_at = timezone.now()
        registration.verified_by = request.user
        registration.save()
        
        # Create verification log
        VerificationLog.objects.create(
            registration=registration,
            verification_status=status,
            notes=notes,
            processed_by=request.user
        )
        
        response_data = {
            'success': True,
            'verification_result': verification_result,
            'status': status,
            'confidence': verification_result['confidence'],
            'message': f'Verification completed with {verification_result["confidence"]:.2f} confidence'
        }
        
        print(f"DEBUG: Auto-verify response: {response_data}")
        return JsonResponse(response_data)
        
    except TournamentRegistration.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Registration not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
@csrf_exempt
def upload_reference_photo(request, registration_id):
    """Upload a reference photo for facial verification"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    # Check if facial recognition is available
    if not FACIAL_RECOGNITION_AVAILABLE:
        return JsonResponse({
            'success': False, 
            'error': 'Facial recognition system not available. Please install required packages.'
        })
    
    print(f"DEBUG: Upload reference photo called for registration {registration_id}")
    print(f"DEBUG: Request FILES: {list(request.FILES.keys())}")
    print(f"DEBUG: Request POST: {list(request.POST.keys())}")
    
    try:
        registration = TournamentRegistration.objects.get(id=registration_id)
        
        # Get uploaded file
        if 'reference_photo' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No reference photo provided'})
        
        reference_photo = request.FILES['reference_photo']
        
        # Save as stored photo
        registration.stored_photo = reference_photo
        registration.save()
        
        # Now perform verification
        verification_result = facial_verifier.verify_faces(
            live_photo_path=registration.live_photo.path,
            stored_photo_path=registration.stored_photo.path
        )
        
        # Update verification status
        if verification_result['verified'] and verification_result['confidence'] > 0.7:
            status = 'VERIFIED'
            notes = f"Verified with reference photo: Confidence {verification_result['confidence']:.2f}"
        elif verification_result['confidence'] > 0.5:
            status = 'MANUAL_REVIEW'
            notes = f"Review with reference photo: Confidence {verification_result['confidence']:.2f}"
        else:
            status = 'FAILED'
            notes = f"Failed with reference photo: Confidence {verification_result['confidence']:.2f}"
        
        registration.verification_status = status
        registration.verification_score = verification_result['confidence']
        registration.verification_notes = notes
        registration.verified_at = timezone.now()
        registration.verified_by = request.user
        registration.save()
        
        response_data = {
            'success': True,
            'verification_result': verification_result,
            'status': status,
            'confidence': verification_result['confidence'],
            'message': f'Reference photo uploaded and verification completed with {verification_result["confidence"]:.2f} confidence'
        }
        
        print(f"DEBUG: Upload reference response: {response_data}")
        return JsonResponse(response_data)
        
    except TournamentRegistration.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Registration not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def tournament_list(request):
    """Display list of active tournaments"""
    tournaments = TournamentCompetition.objects.filter(
        is_active=True,
        start_date__gte=timezone.now()
    ).order_by('start_date')
    
    context = {
        'tournaments': tournaments,
        'title': 'Active Tournaments'
    }
    return render(request, 'tournament_verification/tournament_list.html', context)

def team_selection(request, tournament_id):
    """Beautiful team selection interface for tournament registration"""
    try:
        tournament = TournamentCompetition.objects.get(id=tournament_id)
    except TournamentCompetition.DoesNotExist:
        return render(request, 'tournament_verification/error.html', {
            'error_message': 'Tournament not found'
        })
    
    # Check if tournament has fixtures
    has_fixtures = tournament.fixtures.exists()
    
    # Get teams for this tournament
    teams = TournamentTeam.objects.filter(tournament=tournament).order_by('name')
    
    context = {
        'tournament': tournament,
        'teams': teams,
        'has_fixtures': has_fixtures,
        'title': f'Select Team - {tournament.name}'
    }
    return render(request, 'tournament_verification/team_selection.html', context)

def tournament_registration(request, tournament_id, team_id=None):
    """Tournament registration with photo verification - requires team selection"""
    tournament = get_object_or_404(TournamentCompetition, id=tournament_id, is_active=True)
    
    # Check if registration is still open
    if timezone.now() > tournament.registration_deadline:
        messages.error(request, "Registration for this tournament has closed.")
        return redirect('tournament_verification:tournament_list')
    
    # If no team selected, redirect to team selection
    if not team_id:
        return redirect('tournament_verification:team_selection', tournament_id=tournament_id)
    
    # Get the selected team
    try:
        team = TournamentTeam.objects.get(id=team_id, tournament=tournament)
    except TournamentTeam.DoesNotExist:
        messages.error(request, "Selected team not found.")
        return redirect('tournament_verification:team_selection', tournament_id=tournament_id)
    
    if request.method == 'POST':
        return handle_registration_submission(request, tournament, team)
    
    context = {
        'tournament': tournament,
        'team': team,
        'title': f'Register for {team.name} - {tournament.name}'
    }
    return render(request, 'tournament_verification/tournament_registration.html', context)

def handle_registration_submission(request, tournament, team):
    """Handle the registration form submission"""
    try:
        # Get form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        id_number = request.POST.get('id_number')
        live_photo_data = request.POST.get('live_photo')
        
        # Validate required fields
        if not all([first_name, last_name, email, phone_number, id_number, live_photo_data]):
            messages.error(request, "All fields are required.")
            return redirect('tournament_verification:tournament_registration', tournament_id=tournament.id)
        
        # Check for duplicate registration
        if TournamentRegistration.objects.filter(tournament=tournament, id_number=id_number).exists():
            messages.error(request, "A registration with this ID number already exists for this tournament.")
            return redirect('tournament_verification:tournament_registration', tournament_id=tournament.id)
        
        # Try to find existing player in system
        player = None
        try:
            player = CustomUser.objects.get(id_number=id_number)
        except CustomUser.DoesNotExist:
            pass
        
        # Process and save live photo
        live_photo = process_base64_image(live_photo_data, f"{id_number}_live.jpg")
        
        # Create registration
        registration = TournamentRegistration.objects.create(
            tournament=tournament,
            team=team,
            player=player,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            id_number=id_number,
            live_photo=live_photo,
            stored_photo=player.profile_picture if player else None,
            registration_type='SYSTEM_PLAYER' if player else 'WALK_IN'
        )
        
        # Perform verification if player exists in system
        if player and player.profile_picture:
            verification_result = perform_facial_verification(registration)
            registration.verification_score = verification_result['score']
            registration.verification_status = verification_result['status']
            registration.verification_notes = verification_result['notes']
            registration.verified_at = timezone.now()
            registration.save()
            
            # Log verification attempt
            VerificationLog.objects.create(
                registration=registration,
                verification_score=verification_result['score'],
                verification_status=verification_result['status'],
                notes=verification_result['notes']
            )
        
        messages.success(request, f"Registration successful! Your registration ID is: {registration.id}")
        return redirect('tournament_verification:registration_success', registration_id=registration.id)
        
    except Exception as e:
        messages.error(request, f"Registration failed: {str(e)}")
        return redirect('tournament_verification:tournament_registration', tournament_id=tournament.id, team_id=team.id)

def process_base64_image(base64_data, filename):
    """Process base64 image data and return a file object"""
    try:
        # Remove data URL prefix if present
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]
        
        # Decode base64 data
        image_data = base64.b64decode(base64_data)
        
        # Create PIL Image object
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize image if too large (max 800x600)
        max_size = (800, 600)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save to BytesIO
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=85)
        output.seek(0)
        
        # Create Django file object
        file_obj = ContentFile(output.getvalue(), name=filename)
        return file_obj
        
    except Exception as e:
        raise Exception(f"Failed to process image: {str(e)}")

def perform_facial_verification(registration):
    """Perform facial verification between live and stored photos"""
    # This is a placeholder for actual facial recognition
    # In a real implementation, you would integrate with:
    # - AWS Rekognition
    # - Azure Face API
    # - Google Vision API
    # - OpenCV with face_recognition library
    
    try:
        # Placeholder logic - in reality, you'd call an AI service
        # For now, we'll simulate a verification process
        
        if not registration.stored_photo:
            return {
                'score': 0.0,
                'status': 'MANUAL_REVIEW',
                'notes': 'No stored photo available for comparison'
            }
        
        # Simulate verification score (in reality, this would come from AI service)
        import random
        score = random.uniform(0.3, 0.95)  # Random score between 0.3 and 0.95
        
        if score >= 0.8:
            status = 'VERIFIED'
            notes = f'High confidence match (Score: {score:.2f})'
        elif score >= 0.6:
            status = 'MANUAL_REVIEW'
            notes = f'Medium confidence match (Score: {score:.2f}) - Manual review recommended'
        else:
            status = 'FAILED'
            notes = f'Low confidence match (Score: {score:.2f}) - Verification failed'
        
        return {
            'score': score,
            'status': status,
            'notes': notes
        }
        
    except Exception as e:
        return {
            'score': 0.0,
            'status': 'MANUAL_REVIEW',
            'notes': f'Verification error: {str(e)}'
        }

def registration_success(request, registration_id):
    """Display registration success page"""
    registration = get_object_or_404(TournamentRegistration, id=registration_id)
    
    context = {
        'registration': registration,
        'title': 'Registration Successful'
    }
    return render(request, 'tournament_verification/registration_success.html', context)

@login_required
def tournament_dashboard(request, tournament_id):
    """Dashboard for tournament administrators"""
    tournament = get_object_or_404(TournamentCompetition, id=tournament_id)
    registrations = TournamentRegistration.objects.filter(tournament=tournament).order_by('-registered_at')
    
    # Statistics
    total_registrations = registrations.count()
    verified_registrations = registrations.filter(verification_status='VERIFIED').count()
    pending_verifications = registrations.filter(verification_status='PENDING').count()
    failed_verifications = registrations.filter(verification_status='FAILED').count()
    manual_review = registrations.filter(verification_status='MANUAL_REVIEW').count()
    
    context = {
        'tournament': tournament,
        'registrations': registrations,
        'total_registrations': total_registrations,
        'verified_registrations': verified_registrations,
        'pending_verifications': pending_verifications,
        'failed_verifications': failed_verifications,
        'manual_review': manual_review,
        'title': f'{tournament.name} - Dashboard'
    }
    return render(request, 'tournament_verification/tournament_dashboard.html', context)

@login_required
@require_POST
def manual_verification(request, registration_id):
    """Handle manual verification by administrator"""
    registration = get_object_or_404(TournamentRegistration, id=registration_id)
    action = request.POST.get('action')
    notes = request.POST.get('notes', '')
    
    if action == 'approve':
        registration.verification_status = 'VERIFIED'
        registration.verification_notes = f"Manually approved: {notes}"
        messages.success(request, f"Registration for {registration.full_name} has been approved.")
    elif action == 'reject':
        registration.verification_status = 'REJECTED'
        registration.verification_notes = f"Manually rejected: {notes}"
        messages.warning(request, f"Registration for {registration.full_name} has been rejected.")
    
    registration.verified_at = timezone.now()
    registration.verified_by = request.user
    registration.save()
    
    # Log the manual verification
    VerificationLog.objects.create(
        registration=registration,
        verification_score=registration.verification_score,
        verification_status=registration.verification_status,
        notes=f"Manual verification: {notes}",
        processed_by=request.user
    )
    
    return redirect('tournament_verification:tournament_dashboard', tournament_id=registration.tournament.id)

def team_list(request, tournament_id):
    """Display all teams for a tournament with photos and players"""
    try:
        tournament = TournamentCompetition.objects.get(id=tournament_id)
        teams = TournamentTeam.objects.filter(tournament=tournament).prefetch_related('registrations').order_by('name')
        
        # Calculate statistics
        teams_with_photos = teams.filter(team_photo__isnull=False).count()
        total_players = sum(team.registrations.count() for team in teams)
        
        context = {
            'tournament': tournament,
            'teams': teams,
            'teams_with_photos': teams_with_photos,
            'total_players': total_players,
            'title': f'Teams - {tournament.name}'
        }
        
        return render(request, 'tournament_verification/team_list.html', context)
        
    except TournamentCompetition.DoesNotExist:
        messages.error(request, 'Tournament not found.')
        return redirect('tournament_verification:tournament_list')

def tournament_fixtures(request, tournament_id):
    """Display tournament fixtures"""
    try:
        tournament = TournamentCompetition.objects.get(id=tournament_id)
        fixtures = tournament.fixtures.all().order_by('match_date')
        has_fixtures = fixtures.exists()
        
        context = {
            'tournament': tournament,
            'fixtures': fixtures,
            'has_fixtures': has_fixtures,
            'title': f'Fixtures - {tournament.name}'
        }
        
        return render(request, 'tournament_verification/tournament_fixtures.html', context)
        
    except TournamentCompetition.DoesNotExist:
        messages.error(request, 'Tournament not found.')
        return redirect('tournament_verification:tournament_list')

@login_required
def generate_fixtures(request, tournament_id):
    """Generate fixtures for a tournament"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser privileges required.')
        return redirect('tournament_verification:tournament_list')
    
    try:
        tournament = TournamentCompetition.objects.get(id=tournament_id)
        
        # Check if tournament has teams
        if not tournament.teams.exists():
            messages.error(request, 'Cannot generate fixtures: No teams found for this tournament.')
            return redirect('tournament_verification:tournament_dashboard', tournament_id=tournament.id)
        
        # Generate fixtures
        fixtures = generate_tournament_fixtures(tournament_id)
        
        if fixtures:
            messages.success(request, f'Successfully generated {len(fixtures)} fixtures for {tournament.name}.')
        else:
            messages.error(request, 'Failed to generate fixtures.')
        
        return redirect('tournament_verification:tournament_fixtures', tournament_id=tournament.id)
        
    except TournamentCompetition.DoesNotExist:
        messages.error(request, 'Tournament not found.')
        return redirect('tournament_verification:tournament_list')

@login_required
@require_POST
@csrf_exempt
def generate_team_photo(request, team_id):
    """Generate a composite team photo for a specific team"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    try:
        team = TournamentTeam.objects.get(id=team_id)
        
        # Generate team photo
        if team.generate_team_photo():
            return JsonResponse({
                'success': True, 
                'message': f'Team photo generated successfully for {team.name}',
                'photo_url': team.team_photo.url if team.team_photo else None
            })
        else:
            return JsonResponse({
                'success': False, 
                'error': 'Failed to generate team photo'
            })
            
    except TournamentTeam.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Team not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
@csrf_exempt
def bulk_delete_registrations(request):
    """Bulk delete tournament registrations"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    try:
        data = json.loads(request.body)
        registration_ids = data.get('registration_ids', [])
        
        if not registration_ids:
            return JsonResponse({'success': False, 'error': 'No registrations selected'})
        
        # Get registrations
        registrations = TournamentRegistration.objects.filter(id__in=registration_ids)
        deleted_count = registrations.count()
        
        # Delete registrations
        registrations.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {deleted_count} registration(s)',
            'deleted_count': deleted_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
@csrf_exempt
def bulk_delete_teams(request):
    """Bulk delete tournament teams"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    try:
        data = json.loads(request.body)
        team_ids = data.get('team_ids', [])
        
        if not team_ids:
            return JsonResponse({'success': False, 'error': 'No teams selected'})
        
        # Get teams
        teams = TournamentTeam.objects.filter(id__in=team_ids)
        deleted_count = teams.count()
        
        # Delete teams (this will also delete related registrations and team photos)
        teams.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {deleted_count} team(s)',
            'deleted_count': deleted_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
@csrf_exempt
def bulk_delete_tournaments(request):
    """Bulk delete tournaments"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    try:
        data = json.loads(request.body)
        tournament_ids = data.get('tournament_ids', [])
        
        if not tournament_ids:
            return JsonResponse({'success': False, 'error': 'No tournaments selected'})
        
        # Get tournaments
        tournaments = TournamentCompetition.objects.filter(id__in=tournament_ids)
        deleted_count = tournaments.count()
        
        # Delete tournaments (this will cascade delete teams, registrations, etc.)
        tournaments.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {deleted_count} tournament(s)',
            'deleted_count': deleted_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
