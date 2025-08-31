from django.core.management.base import BaseCommand
from membership.models import RegistrationWorkflow

class Command(BaseCommand):
    help = 'Updates the progress of all registration workflows'

    def handle(self, *args, **options):
        self.stdout.write('Starting workflow update process...')
        workflows = RegistrationWorkflow.objects.all()
        updated_count = 0
        for workflow in workflows:
            workflow.update_progress()
            updated_count += 1
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} workflows.'))
