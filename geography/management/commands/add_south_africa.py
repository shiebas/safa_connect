from django.core.management.base import BaseCommand
from geography.models import Country

class Command(BaseCommand):
    help = 'Add South Africa to the Country table if it does not exist'

    def handle(self, *args, **kwargs):
        country_name = "South Africa"
        country_code = "ZAF"

        try:
            country, created = Country.objects.get_or_create(
                name=country_name,
                defaults={
                    'code': country_code,
                    'description': "Country in Southern Africa"
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Successfully added {country_name} to the Country table."))
            else:
                self.stdout.write(self.style.WARNING(f"{country_name} already exists in the Country table."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error adding {country_name}: {str(e)}"))
