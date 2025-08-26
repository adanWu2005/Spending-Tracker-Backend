from django.core.management.base import BaseCommand
from api.models import DataRetentionPolicy, AccessProvisioning, ZeroTrustArchitecture, CentralizedIAM

class Command(BaseCommand):
    help = 'Initialize security attestations'

    def handle(self, *args, **options):
        self.stdout.write('Initializing security attestations...')
        
        # Create all security attestation records
        DataRetentionPolicy.objects.get_or_create(defaults={'is_implemented': True})
        AccessProvisioning.objects.get_or_create(defaults={'is_implemented': True})
        ZeroTrustArchitecture.objects.get_or_create(defaults={'is_implemented': True})
        CentralizedIAM.objects.get_or_create(defaults={'is_implemented': True})
        
        self.stdout.write(
            self.style.SUCCESS('Successfully initialized all security attestations')
        )
