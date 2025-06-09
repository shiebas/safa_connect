from django.core.management.base import BaseCommand
from django.db import transaction
from geography.models import Province, Region, LocalFootballAssociation

class Command(BaseCommand):
    help = 'Fix Free State regions to be sequential starting from region ID 9'
    
    def handle(self, *args, **options):
        self.stdout.write('🔧 Fixing Free State regions...')
        
        # Free State regions (should start from ID 9 after Eastern Cape 1-8)
        freestate_regions = {
            'Fezile Dabi': [
                'Parys LFA', 'Sasolburg LFA', 'Heilbron LFA', 'Vredefort LFA',
                'Oranjeville LFA', 'Deneysville LFA'
            ],
            'Lejweleputswa': [
                'Kimberley LFA', 'Boshof LFA', 'Dealesville LFA', 'Hertzogville LFA',
                'Hoopstad LFA', 'Bloemhof LFA'
            ],
            'Mangaung': [
                'Bloemfontein LFA', 'Botshabelo LFA', 'Thaba Nchu LFA', 'Dewetsdorp LFA',
                'Wepener LFA', 'Van Stadensrus LFA'
            ],
            'Thabo Mofutsanyana': [
                'Phuthaditjhaba LFA', 'Bethlehem LFA', 'Harrismith LFA', 'Kestell LFA',
                'Clarens LFA', 'Fouriesburg LFA'
            ],
            'Xhariep': [
                'Trompsburg LFA', 'Philippolis LFA', 'Springfontein LFA', 'Fauresmith LFA',
                'Jagersfontein LFA', 'Koffiefontein LFA'
            ]
        }
        
        try:
            with transaction.atomic():
                province = Province.objects.get(name='Free State')
                
                # Delete existing Free State regions
                self.stdout.write('\n🗑️  Deleting current Free State regions...')
                deleted_count = Region.objects.filter(province=province).delete()
                self.stdout.write(f'   Deleted: {deleted_count}')
                
                # Create Free State regions starting from ID 9
                region_id = 9
                total_lfas = 0
                
                for region_name, lfa_names in freestate_regions.items():
                    # Create region
                    region = Region(
                        id=region_id,
                        name=region_name,
                        province=province
                    )
                    region.save()
                    self.stdout.write(f'   ✅ Created ID {region_id}: {region_name}')
                    
                    # Create LFAs
                    for lfa_name in lfa_names:
                        LocalFootballAssociation.objects.create(
                            name=lfa_name,
                            region=region
                        )
                        total_lfas += 1
                    
                    self.stdout.write(f'     Added {len(lfa_names)} LFAs')
                    region_id += 1
                
                # Verify Free State
                self.stdout.write(f'\n✅ Free State regions created:')
                fs_regions = Region.objects.filter(province=province).order_by('id')
                for region in fs_regions:
                    lfas_count = region.localfootballassociation_set.count()
                    self.stdout.write(f'   ID {region.id}: {region.name} ({lfas_count} LFAs)')
                
                self.stdout.write(
                    self.style.SUCCESS(f'\n🎉 Free State fixed! {fs_regions.count()} regions, {total_lfas} LFAs')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {str(e)}')
            )
