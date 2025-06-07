from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Q
import time

@staff_member_required
def generate_all_safa_ids(request):
    """Generate SAFA IDs for all entities that need them"""
    from accounts.models import CustomUser
    from django.utils.crypto import get_random_string
    from geography.models import Club, Region, LocalFootballAssociation
    from membership.models import Member
    
    if request.method == 'POST':
        # Track stats
        stats = {}
        
        # Get unique existing IDs to avoid duplicates
        all_ids = set()
        models = [CustomUser, Member, Club, Region, LocalFootballAssociation]
        for model in models:
            # Only collect safa_id if the model has this field
            if hasattr(model, 'safa_id'):
                ids = model.objects.exclude(Q(safa_id=None) | Q(safa_id='')).values_list('safa_id', flat=True)
                all_ids.update(ids)
                
        # Process each model
        for model in models:
            model_name = model.__name__
            
            if not hasattr(model, 'safa_id'):
                stats[model_name] = {'status': 'skipped', 'reason': 'No safa_id field'}
                continue
            
            # Get objects needing IDs
            objects = model.objects.filter(Q(safa_id=None) | Q(safa_id=''))
            count = objects.count()
            
            if count == 0:
                stats[model_name] = {'status': 'complete', 'count': 0}
                continue
                
            # Generate and assign IDs
            updated = 0
            for obj in objects:
                # Generate new unique ID
                while True:
                    new_id = get_random_string(length=5, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
                    if new_id not in all_ids:
                        break
                
                # Assign and save
                all_ids.add(new_id)
                obj.safa_id = new_id
                obj.save(update_fields=['safa_id'])
                updated += 1
                
                # Avoid overloading the server
                if updated % 50 == 0:
                    time.sleep(0.1)
                
            stats[model_name] = {'status': 'success', 'count': updated}
            
        return JsonResponse({'success': True, 'stats': stats})
    else:
        # Get counts of missing IDs
        missing_ids = {}
        models = [CustomUser, Member, Club, Region, LocalFootballAssociation]
        
        for model in models:
            model_name = model.__name__
            if hasattr(model, 'safa_id'):
                total = model.objects.count()
                missing = model.objects.filter(Q(safa_id=None) | Q(safa_id='')).count()
                missing_ids[model_name] = {'total': total, 'missing': missing}
        
        return render(request, 'admin/tools/generate_all_ids.html', {'missing_ids': missing_ids})

@staff_member_required
def safa_id_coverage(request):
    """Show report on SAFA ID coverage across all models"""
    from django.db.models import Count, Q
    from accounts.models import CustomUser
    from membership.models import Member, Player
    from geography.models import Club, Region, Province, Association, LocalFootballAssociation
    
    models = [
        {'name': 'Users', 'model': CustomUser},
        {'name': 'Members', 'model': Member},
        {'name': 'Players', 'model': Player},
        {'name': 'Clubs', 'model': Club},
        {'name': 'Regions', 'model': Region},
        {'name': 'Provinces', 'model': Province},
        {'name': 'Associations', 'model': Association},
        {'name': 'Local Football Associations', 'model': LocalFootballAssociation},
    ]
    
    stats = []
    for item in models:
        model = item['model']
        if not hasattr(model, 'safa_id'):
            continue
            
        # Get stats
        total = model.objects.count()
        missing = model.objects.filter(Q(safa_id=None) | Q(safa_id='')).count()
        coverage = ((total - missing) / total * 100) if total > 0 else 100
        
        stats.append({
            'name': item['name'],
            'total': total,
            'missing': missing,
            'coverage': coverage,
            'link': f"/admin/{model._meta.app_label}/{model._meta.model_name}/?safa_id__exact="
        })
        
    return render(request, 'admin/tools/coverage_report.html', {'stats': stats})
