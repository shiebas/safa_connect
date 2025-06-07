from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Q
from django.utils.crypto import get_random_string
import time

@staff_member_required
def generate_all_safa_ids(request):
    """Generate SAFA IDs for all entities that don't have them"""
    try:
        from accounts.models import CustomUser
        
        # Try to import optional models
        try:
            from geography.models import Club, Region, LocalFootballAssociation
            has_geography = True
        except ImportError:
            has_geography = False
            
        try:
            from membership.models import Member
            has_membership = True
        except ImportError:
            has_membership = False
            
        # Get model stats
        stats = []
        
        # Users stats
        user_total = CustomUser.objects.count()
        user_missing = CustomUser.objects.filter(Q(safa_id__isnull=True) | Q(safa_id='')).count()
        stats.append({
            'name': 'Users',
            'total': user_total,
            'missing': user_missing,
            'model_type': 'user'
        })
        
        # Geography models
        if has_geography:
            club_total = Club.objects.count()
            club_missing = Club.objects.filter(Q(safa_id__isnull=True) | Q(safa_id='')).count()
            stats.append({
                'name': 'Clubs',
                'total': club_total,
                'missing': club_missing,
                'model_type': 'club'
            })
            
            region_total = Region.objects.count()
            region_missing = Region.objects.filter(Q(safa_id__isnull=True) | Q(safa_id='')).count()
            stats.append({
                'name': 'Regions',
                'total': region_total,
                'missing': region_missing,
                'model_type': 'region'
            })
            
            lfa_total = LocalFootballAssociation.objects.count()
            lfa_missing = LocalFootballAssociation.objects.filter(Q(safa_id__isnull=True) | Q(safa_id='')).count()
            stats.append({
                'name': 'Local Football Associations',
                'total': lfa_total,
                'missing': lfa_missing,
                'model_type': 'lfa'
            })
        
        # Membership models
        if has_membership:
            member_total = Member.objects.count()
            member_missing = Member.objects.filter(Q(safa_id__isnull=True) | Q(safa_id='')).count()
            stats.append({
                'name': 'Members',
                'total': member_total,
                'missing': member_missing,
                'model_type': 'member'
            })
            
        # Handle POST for actual generation
        if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            results = {}
            model_types = request.POST.getlist('model_type[]')
            
            # Generate for users
            if 'user' in model_types:
                count = 0
                for user in CustomUser.objects.filter(Q(safa_id__isnull=True) | Q(safa_id='')):
                    user.generate_safa_id()
                    user.save()
                    count += 1
                results['users'] = {'count': count, 'status': 'success'}
                
            # Generate for clubs
            if has_geography and 'club' in model_types:
                count = 0
                for club in Club.objects.filter(Q(safa_id__isnull=True) | Q(safa_id='')):
                    # Generate code
                    while True:
                        code = get_random_string(length=5, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
                        if not Club.objects.filter(safa_id=code).exists():
                            break
                    club.safa_id = code
                    club.save(update_fields=['safa_id'])
                    count += 1
                results['clubs'] = {'count': count, 'status': 'success'}
                
            # Return JSON response
            return JsonResponse({'success': True, 'results': results})
            
        return render(request, 'admin/tools/generate_safa_ids.html', {
            'stats': stats,
            'title': 'Generate SAFA IDs',
        })
    except Exception as e:
        import traceback
        return render(request, 'admin/tools/error.html', {
            'title': 'Error',
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@staff_member_required
def safa_id_coverage(request):
    """Show SAFA ID coverage report"""
    try:
        from accounts.models import CustomUser
        
        # Try to import optional models
        try:
            from geography.models import Club, Region
            has_geography = True
        except ImportError:
            has_geography = False
            
        try:
            from membership.models import Member
            has_membership = True
        except ImportError:
            has_membership = False
            
        # Get stats
        stats = []
        
        # Users stats
        user_total = CustomUser.objects.count()
        user_missing = CustomUser.objects.filter(Q(safa_id__isnull=True) | Q(safa_id='')).count()
        user_coverage = 100 - (user_missing / user_total * 100 if user_total > 0 else 0)
        stats.append({
            'name': 'Users',
            'total': user_total,
            'missing': user_missing,
            'coverage': user_coverage,
            'url': '/admin/accounts/customuser/?safa_id__isnull=True'
        })
        
        # Geography models
        if has_geography:
            club_total = Club.objects.count()
            club_missing = Club.objects.filter(Q(safa_id__isnull=True) | Q(safa_id='')).count()
            club_coverage = 100 - (club_missing / club_total * 100 if club_total > 0 else 0)
            stats.append({
                'name': 'Clubs',
                'total': club_total,
                'missing': club_missing,
                'coverage': club_coverage,
                'url': '/admin/geography/club/?safa_id__isnull=True'
            })
            
        # Membership models
        if has_membership:
            member_total = Member.objects.count()
            member_missing = Member.objects.filter(Q(safa_id__isnull=True) | Q(safa_id='')).count()
            member_coverage = 100 - (member_missing / member_total * 100 if member_total > 0 else 0)
            stats.append({
                'name': 'Members',
                'total': member_total,
                'missing': member_missing,
                'coverage': member_coverage,
                'url': '/admin/membership/member/?safa_id__isnull=True'
            })
        
        # Calculate overall coverage
        total_items = sum(stat['total'] for stat in stats)
        total_missing = sum(stat['missing'] for stat in stats)
        overall_coverage = 100 - (total_missing / total_items * 100 if total_items > 0 else 0)
        
        return render(request, 'admin/tools/coverage_report.html', {
            'stats': stats,
            'overall': {
                'total': total_items,
                'missing': total_missing,
                'coverage': overall_coverage
            },
            'title': 'SAFA ID Coverage Report',
        })
    except Exception as e:
        import traceback
        return render(request, 'admin/tools/error.html', {
            'title': 'Error',
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@staff_member_required
def generate_qr_codes(request):
    """Generate QR codes for entities"""
    try:
        return render(request, 'admin/tools/generate_qr_codes.html', {
            'title': 'Generate QR Codes',
        })
    except Exception as e:
        import traceback
        return render(request, 'admin/tools/error.html', {
            'title': 'Error',
            'error': str(e),
            'traceback': traceback.format_exc()
        })
