from django.utils.translation import gettext_lazy as _

# Import safely - use django admin as fallback
try:
    # Try Django admin_tools first
    from admin_tools.dashboard import modules, Dashboard
except ImportError:
    # If admin_tools is not available, use standard Django admin components
    from django.contrib.admin import AdminSite
    from django.apps import apps
    
    # Create basic replacements for admin_tools classes
    class Dashboard:
        def __init__(self, *args, **kwargs):
            self.children = []
        
        def init_with_context(self, context):
            pass
    
    class Module:
        def __init__(self, title='', **kwargs):
            self.title = title
            self.__dict__.update(kwargs)
    
    class modules:
        class LinkList(Module):
            def __init__(self, title, children=None, **kwargs):
                super().__init__(title, **kwargs)
                self.children = children or []
        
        class DashboardModule(Module):
            pass
        
        class AppList(Module):
            def __init__(self, title, exclude=None, models=None, **kwargs):
                super().__init__(title, **kwargs)
                self.exclude = exclude
                self.models = models

from django.db.models import Count, Q

class CustomIndexDashboard(Dashboard):
    """
    Custom dashboard for the admin site
    """
    def init_with_context(self, context):
        # Ensure models are imported only when needed to avoid circular imports
        self.children.append(modules.LinkList(
            _('Quick Links'),
            layout='inline',
            children=[
                {'title': _('Generate Missing SAFA IDs'), 'url': '/admin/tools/generate-all-safa-ids/', 'external': False},
                {'title': _('Print Membership Cards'), 'url': '/admin/membership/member/print-membership-cards/', 'external': False},
                {'title': _('View SAFA ID Coverage Report'), 'url': '/admin/tools/safa-id-coverage/', 'external': False},
                {'title': _('Return to admin site'), 'url': '/admin/'}
            ]
        ))
        
        # Add SAFA ID status overview
        try:
            # Import models inside the try block to avoid import errors
            from accounts.models import CustomUser
            from geography.models import Club, Region, Association
            
            # Try to get stats - first check if Member exists
            try:
                from membership.models import Member, Player
                has_member_model = True
            except ImportError:
                has_member_model = False
            
            # User stats
            user_stats = CustomUser.objects.aggregate(
                total=Count('id'),
                missing=Count('id', filter=Q(safa_id__isnull=True) | Q(safa_id=''))
            )
            
            # Member stats if available
            if has_member_model:
                member_stats = Member.objects.aggregate(
                    total=Count('id'),
                    missing=Count('id', filter=Q(safa_id__isnull=True) | Q(safa_id=''))
                )
            else:
                member_stats = {'total': 0, 'missing': 0}
            
            # Club stats
            club_stats = Club.objects.aggregate(
                total=Count('id'),
                missing=Count('id', filter=Q(safa_id__isnull=True) | Q(safa_id=''))
            )
            
            safa_id_stats = [
                {'title': 'Users', 'total': user_stats['total'], 'missing': user_stats['missing']},
                {'title': 'Members', 'total': member_stats['total'], 'missing': member_stats['missing']},
                {'title': 'Clubs', 'total': club_stats['total'], 'missing': club_stats['missing']},
            ]
            
            self.children.append(modules.DashboardModule(
                title=_('SAFA ID Coverage'),
                pre_content='''
                <style>
                    .safa-id-stats {width: 100%; border-collapse: collapse;}
                    .safa-id-stats th, .safa-id-stats td {padding: 8px; text-align: center; border-bottom: 1px solid #ddd;}
                    .safa-id-stats .missing {color: #e74c3c;}
                    .safa-id-stats .complete {color: #2ecc71;}
                    .safa-id-stats .progress-container {width: 100%; background-color: #f3f3f3; border-radius: 5px;}
                    .safa-id-stats .progress-bar {height: 10px; border-radius: 5px;}
                </style>
                <table class="safa-id-stats">
                    <tr>
                        <th>Entity</th>
                        <th>Total</th>
                        <th>Missing</th>
                        <th>Coverage</th>
                    </tr>
                ''',
                content='\n'.join([
                    f'''
                    <tr>
                        <td>{stat['title']}</td>
                        <td>{stat['total']}</td>
                        <td class="{'missing' if stat['missing'] > 0 else ''}">{stat['missing']}</td>
                        <td>
                            <div class="progress-container">
                                <div class="progress-bar" style="width: {100 - (stat['missing']/stat['total']*100 if stat['total'] > 0 else 0)}%; background-color: {'#2ecc71' if stat['missing'] == 0 else '#e74c3c'}"></div>
                            </div>
                            {100 - (stat['missing']/stat['total']*100 if stat['total'] > 0 else 0):.1f}%
                        </td>
                    </tr>
                    '''
                    for stat in safa_id_stats
                ]),
                post_content='</table>'
            ))
        except Exception as e:
            # If any error occurs, show simpler module
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in dashboard: {str(e)}")
            
            self.children.append(modules.LinkList(
                _('SAFA ID Management'),
                children=[
                    {'title': _('Generate Missing SAFA IDs'), 'url': '/admin/tools/generate-all-safa-ids/'},
                    {'title': _('View Users Without SAFA IDs'), 'url': '/admin/accounts/customuser/?safa_id__exact='}
                ]
            ))
        
        # Other default modules
        self.children.append(modules.AppList(
            _('Applications'),
            exclude=('django.contrib.*',),
        ))
        
        self.children.append(modules.AppList(
            _('Administration'),
            models=('django.contrib.*',),
        ))
