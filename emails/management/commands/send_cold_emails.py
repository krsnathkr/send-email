from django.core.management.base import BaseCommand
from emails.services import EmailEngine
import os

class Command(BaseCommand):
    help = 'Send cold emails from a CSV file using a Markdown template'

    def add_arguments(self, parser):
        parser.add_argument('--csv', type=str, required=True, help='Path to CSV file containing contacts')
        parser.add_argument('--template', type=str, required=True, help='Path to Markdown template file')
        parser.add_argument('--subject', type=str, default='Cold Outreach', help='Default subject (can be overridden by template)')
        parser.add_argument('--dry-run', action='store_true', help='Process files but do not actually send emails')

    def handle(self, *args, **options):
        csv_path = options['csv']
        template_path = options['template']
        subject = options['subject']
        dry_run = options['dry_run']

        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f"CSV file not found: {csv_path}"))
            return
            
        if not os.path.exists(template_path):
            self.stdout.write(self.style.ERROR(f"Template file not found: {template_path}"))
            return

        self.stdout.write(self.style.SUCCESS(f"Starting campaign... (Dry Run: {dry_run})"))
        
        # Determine Campaign Name from CSV filename
        campaign_name = os.path.basename(csv_path).rsplit('.', 1)[0]
        self.stdout.write(f"Campaign Name: {campaign_name}")

        results = EmailEngine.send_campaign(
            campaign_name=campaign_name,
            subject=subject,
            template_path=template_path,
            csv_path=csv_path,
            dry_run=dry_run
        )
        
        # Report
        import_stats = results['import_stats']
        self.stdout.write(f"Contacts Processed: {import_stats['created']} created, {import_stats['updated']} updated.")
        
        if import_stats['errors']:
            self.stdout.write(self.style.WARNING(f"Import Errors: {len(import_stats['errors'])}"))
            for err in import_stats['errors']:
                self.stdout.write(f"  - {err}")

        self.stdout.write(self.style.SUCCESS(f"Emails Sent: {results['sent']}"))
        
        if results['errors']:
            self.stdout.write(self.style.ERROR(f"Sending Errors: {len(results['errors'])}"))
            for err in results['errors']:
                self.stdout.write(f"  - {err}")
                
        self.stdout.write(self.style.SUCCESS("Done."))
