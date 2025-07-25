# member_type_analyzer.py
"""
Analyze all member types in your SAFA system to understand the full scope
This includes Players, Officials (referees, coaches, club chairpersons), and other roles
"""

import django
import os
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safa_global.settings')
django.setup()

from django.db import models
from django.apps import apps
from django.contrib.auth import get_user_model

def analyze_member_types():
    """Analyze all member-related models in the system"""
    
    print("🔍 ANALYZING MEMBER TYPES IN SAFA SYSTEM")
    print("="*60)
    
    # Get all models
    all_models = apps.get_models()
    
    # Find base Member model
    member_models = []
    user_models = []
    position_models = []
    
    for model in all_models:
        model_name = model.__name__
        
        # Check for Member-related models
        if 'member' in model_name.lower():
            member_models.append(model)
        
        # Check for User-related models
        if 'user' in model_name.lower():
            user_models.append(model)
        
        # Check for Position/Role models
        if any(keyword in model_name.lower() for keyword in ['position', 'role', 'official']):
            position_models.append(model)
    
    print("\n📊 MEMBER-RELATED MODELS:")
    analyze_model_group(member_models, "Member Models")
    
    print("\n👤 USER-RELATED MODELS:")
    analyze_model_group(user_models, "User Models")
    
    print("\n🏅 POSITION/ROLE MODELS:")
    analyze_model_group(position_models, "Position/Role Models")
    
    # Check inheritance patterns
    print("\n🔗 INHERITANCE ANALYSIS:")
    check_inheritance_patterns(all_models)
    
    # Check for specific SAFA roles
    print("\n⚽ SAFA-SPECIFIC ROLES:")
    check_safa_roles()

def analyze_model_group(models, group_name):
    """Analyze a group of models"""
    if not models:
        print(f"   ❌ No {group_name} found")
        return
    
    for model in models:
        print(f"\n   📋 {model.__name__}")
        print(f"       App: {model._meta.app_label}")
        print(f"       Table: {model._meta.db_table}")
        
        # Check inheritance
        mro = model.__mro__[1:-1]  # Skip self and object
        if mro:
            parent_names = [cls.__name__ for cls in mro if hasattr(cls, '_meta')]
            print(f"       Inherits from: {' -> '.join(parent_names)}")
        
        # Check fields
        fields = model._meta.get_fields()
        field_names = [f.name for f in fields if not f.is_relation or f.many_to_one or f.one_to_one]
        if field_names:
            print(f"       Key fields: {', '.join(field_names[:8])}{'...' if len(field_names) > 8 else ''}")
        
        # Check if it has instances
        try:
            count = model.objects.count()
            print(f"       Instances: {count}")
        except Exception as e:
            print(f"       Instances: Error counting ({str(e)[:50]})")

def check_inheritance_patterns(all_models):
    """Check for inheritance patterns across all models"""
    
    # Find models that inherit from common bases
    inheritance_tree = {}
    
    for model in all_models:
        for parent in model.__mro__[1:]:  # Skip self
            if hasattr(parent, '_meta') and parent != models.Model:
                parent_name = parent.__name__
                if parent_name not in inheritance_tree:
                    inheritance_tree[parent_name] = []
                inheritance_tree[parent_name].append(model.__name__)
    
    # Show inheritance patterns
    for parent, children in inheritance_tree.items():
        if len(children) > 1:  # Only show if multiple children
            print(f"\n   🌳 {parent}")
            for child in children:
                print(f"       └── {child}")

def check_safa_roles():
    """Check for specific SAFA roles and member types"""
    
    roles_to_check = [
        'Player', 'Official', 'Referee', 'Coach', 'Manager',
        'Chairman', 'Secretary', 'Treasurer', 'Administrator'
    ]
    
    found_models = {}
    
    all_models = apps.get_models()
    
    for role in roles_to_check:
        for model in all_models:
            if role.lower() in model.__name__.lower():
                found_models[role] = model
                break
    
    print("\n   🎯 SAFA Role Models Found:")
    for role in roles_to_check:
        if role in found_models:
            model = found_models[role]
            print(f"       ✅ {role}: {model.__name__} ({model._meta.app_label})")
            
            # Check if it's a Member subclass
            is_member_subclass = any('Member' in str(parent) for parent in model.__mro__)
            if is_member_subclass:
                print(f"           🔗 Inherits from Member")
            else:
                print(f"           ⚠️  Does NOT inherit from Member")
        else:
            print(f"       ❌ {role}: Not found")
    
    # Check Position model if it exists
    try:
        from accounts.models import Position
        positions = Position.objects.all()
        print(f"\n   📋 POSITIONS IN DATABASE ({positions.count()}):")
        for pos in positions[:10]:  # Show first 10
            print(f"       - {pos.name}")
        if positions.count() > 10:
            print(f"       ... and {positions.count() - 10} more")
    except ImportError:
        print("\n   ❌ Position model not found in accounts.models")
    except Exception as e:
        print(f"\n   ⚠️  Error accessing Position model: {str(e)}")

def check_member_data_integrity():
    """Check data integrity issues"""
    print("\n🔍 DATA INTEGRITY CHECK:")
    print("="*40)
    
    try:
        # Try to import and check Member model
        from membership.models import Member
        
        total_members = Member.objects.count()
        print(f"   📊 Total Members: {total_members}")
        
        # Check for Players
        try:
            from registration.models import Player
            total_players = Player.objects.count()
            
            # Check for Members who should be Players but aren't
            from membership.models import Invoice
            player_invoices = Invoice.objects.filter(
                invoice_type='PLAYER_REGISTRATION',
                player__isnull=True,
                member__isnull=False
            ).count()
            
            print(f"   ⚽ Total Players: {total_players}")
            print(f"   ⚠️  Members with player invoices but no Player instance: {player_invoices}")
            
        except ImportError:
            print("   ❌ Player model not found")
        
        # Check for Officials
        try:
            from registration.models import Official
            total_officials = Official.objects.count()
            
            # Check for Members who should be Officials but aren't
            official_invoices = Invoice.objects.filter(
                invoice_type='OFFICIAL_REGISTRATION',
                official__isnull=True,
                member__isnull=False
            ).count()
            
            print(f"   🏅 Total Officials: {total_officials}")
            print(f"   ⚠️  Members with official invoices but no Official instance: {official_invoices}")
            
        except ImportError:
            print("   ❌ Official model not found")
        
        # Check general Member types
        members_without_subtype = Member.objects.filter(
            player__isnull=True,
            official__isnull=True
        ).count()
        
        print(f"   👥 Members without specific subtype: {members_without_subtype}")
        
    except ImportError as e:
        print(f"   ❌ Cannot import required models: {e}")
    except Exception as e:
        print(f"   ⚠️  Error checking data: {e}")

def generate_fix_priority():
    """Generate priority list for fixes"""
    print("\n🎯 FIX PRIORITY ANALYSIS:")
    print("="*40)
    
    priorities = []
    
    try:
        # Check Player issues
        from registration.models import Player
        from membership.models import Member, Invoice
        
        player_invoice_issues = Invoice.objects.filter(
            invoice_type='PLAYER_REGISTRATION',
            player__isnull=True,
            member__isnull=False
        ).count()
        
        if player_invoice_issues > 0:
            priorities.append({
                'type': 'Player Registration',
                'count': player_invoice_issues,
                'priority': 'HIGH',
                'description': 'Members with player invoices need Player instances'
            })
    
    except ImportError:
        priorities.append({
            'type': 'Player Model',
            'count': 0,
            'priority': 'CRITICAL',
            'description': 'Player model missing - inheritance not set up'
        })
    
    try:
        # Check Official issues
        from registration.models import Official
        
        official_invoice_issues = Invoice.objects.filter(
            invoice_type='OFFICIAL_REGISTRATION',
            official__isnull=True,
            member__isnull=False
        ).count()
        
        if official_invoice_issues > 0:
            priorities.append({
                'type': 'Official Registration',
                'count': official_invoice_issues,
                'priority': 'HIGH',
                'description': 'Members with official invoices need Official instances'
            })
    
    except ImportError:
        priorities.append({
            'type': 'Official Model',
            'count': 0,
            'priority': 'CRITICAL',
            'description': 'Official model missing - inheritance not set up'
        })
    
    # Sort by priority
    priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    priorities.sort(key=lambda x: priority_order.get(x['priority'], 4))
    
    for i, item in enumerate(priorities, 1):
        priority_icon = "🔴" if item['priority'] == 'CRITICAL' else "🟠" if item['priority'] == 'HIGH' else "🟡"
        print(f"   {i}. {priority_icon} {item['priority']} - {item['type']}")
        print(f"       Issue count: {item['count']}")
        print(f"       Description: {item['description']}\n")

if __name__ == "__main__":
    try:
        analyze_member_types()
        check_member_data_integrity()
        generate_fix_priority()
        
        print("\n" + "="*60)
        print("✅ ANALYSIS COMPLETE")
        print("="*60)
        print("\nThis analysis shows:")
        print("• What member types exist in your system")
        print("• Which models use proper inheritance")
        print("• Data integrity issues that need fixing")
        print("• Priority order for implementing fixes")
        
    except Exception as e:
        print(f"❌ Error running analysis: {e}")
        print("\nMake sure you're running this from your Django project directory")
        print("and that your Django settings are properly configured.")
