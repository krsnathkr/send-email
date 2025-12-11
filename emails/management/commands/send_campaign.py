from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMultiAlternatives
from django.template import Template, Context
from django.conf import settings
from emails.models import Contact, EmailCampaign, EmailLog
import csv
import markdown
import os
import time


class Command(BaseCommand):
    help = 'Send bulk emails from CSV using a Markdown template'

    def add_arguments(self, parser):
        parser.add_argument('--csv', type=str, required=True, help='Path to the CSV file')
        parser.add_argument('--template', type=str, required=True, help='Path to the Markdown template file')
        parser.add_argument('--subject', type=str, required=True, help='Subject of the email')
        parser.add_argument('--name', type=str, required=True, help='Name of the campaign')
        parser.add_argument('--delay', type=int, default=10, help='Delay between emails in seconds (default: 10)')
        parser.add_argument('--dry-run', action='store_true', help='Simulate sending without actually sending')


    def handle(self, *args, **options):
        csv_path = options['csv']
        template_path = options['template']
        # Subject from CLI is fallback/override
        cli_subject = options['subject']
        campaign_name = options['name']
        delay = options['delay']
        dry_run = options['dry_run']


        if not os.path.exists(csv_path):
            raise CommandError(f'CSV file not found: {csv_path}')
        
        if not os.path.exists(template_path):
            raise CommandError(f'Template file not found: {template_path}')

        # Read Template
        with open(template_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Parse Subject from Template (if present)
        template_subject = None
        body_start_idx = 0
        
        if lines and lines[0].strip().lower().startswith('subject:'):
            # Try to get subject from same line
            first_line_content = lines[0][8:].strip()
            if first_line_content:
                template_subject = first_line_content
                body_start_idx = 1
            else:
                # Try next line if strictly following "Subject:\nActual Subject"
                if len(lines) > 1 and lines[1].strip():
                    template_subject = lines[1].strip()
                    body_start_idx = 2
                else:
                    body_start_idx = 1 # Just skip the Subject: line
        
        template_content_md = ''.join(lines[body_start_idx:])
        
        # Use template subject if found, otherwise CLI subject
        final_subject_template = template_subject if template_subject else cli_subject

        # Create Campaign
        campaign, created = EmailCampaign.objects.get_or_create(
            name=campaign_name,
            defaults={'subject': final_subject_template, 'template_path': template_path}
        )

        # Read CSV
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Normalize headers - strip whitespace
            reader.fieldnames = [name.strip() for name in reader.fieldnames]
            
            for row in reader:
                email = row.get('email') or row.get('Email') or row.get('EMAIL')
                if not email:
                    self.stdout.write(self.style.WARNING(f"Skipping row with no email: {row}"))
                    continue
                
                # Create/Update Contact
                contact, _ = Contact.objects.update_or_create(
                    email=email,
                    defaults={
                        'first_name': row.get('first_name', '') or row.get('Name', '').split(' ')[0],
                        'last_name': row.get('last_name', '') or ' '.join(row.get('Name', '').split(' ')[1:]),
                        'company': row.get('company', '') or row.get('Company', ''),
                        'extra_data': row # Store everything just in case
                    }
                )

                # Prepare Context
                context_data = row.copy()
                context_data.update({
                    'email': contact.email,
                    'first_name': contact.first_name,
                    'last_name': contact.last_name,
                    'company': contact.company,
                })

                # --- RENDER SUBJECT ---
                rendered_subject = final_subject_template
                # 1. Try [Key] replacement (for columns present in CSV)
                for key, value in context_data.items():
                    if key and value:
                        rendered_subject = rendered_subject.replace(f'[{key}]', str(value))
                
                # 2. Try {{ Key }} replacement (Django style)
                django_subject_tmpl = Template(rendered_subject)
                django_context = Context(context_data)
                rendered_subject = django_subject_tmpl.render(django_context)


                # --- RENDER BODY ---
                # 1. [Key] Replacement
                # We iterate over the CSV keys and replace [Key] with Value.
                # This avoids replacing things like [Link Text](url) unless "Link Text" is actually a CSV column.
                
                rendered_md = template_content_md
                for key, value in context_data.items():
                    if key: # ensure key is not None/Empty
                        # Simple string replace
                        # Note: This is case-sensitive based on CSV header.
                        # If CSV has "Name", it replaces [Name].
                        placeholder = f'[{key}]'
                        rendered_md = rendered_md.replace(placeholder, str(value))
                
                # 2. Django Template Replacement (fallback/advanced)
                django_template = Template(rendered_md)
                rendered_md = django_template.render(django_context)

                # 3. Convert Markdown to HTML
                html_content = markdown.markdown(rendered_md)

                if dry_run:
                    self.stdout.write(f"\n[Dry Run] Sending to {email}...")
                    self.stdout.write(f"Subject: {rendered_subject}")
                    self.stdout.write(f"--- Body (Full Preview) ---")
                    self.stdout.write(rendered_md)
                    self.stdout.write(f"--------------------------------\n")
                    continue

                # Send Email
                try:
                    msg = EmailMultiAlternatives(
                        subject=rendered_subject,
                        body=rendered_md, # Text version
                        from_email=settings.EMAIL_HOST_USER,
                        to=[email]
                    )
                    msg.attach_alternative(html_content, "text/html")
                    msg.send()

                    # Log Success
                    EmailLog.objects.create(
                        campaign=campaign,
                        contact=contact,
                        subject=rendered_subject,
                        status='sent'
                    )
                    self.stdout.write(self.style.SUCCESS(f"Sent to {email}"))
                
                except Exception as e:
                    # Log Failure
                    EmailLog.objects.create(
                        campaign=campaign,
                        contact=contact,
                        subject=rendered_subject,
                        status='failed',
                        error_message=str(e)
                    )
                    self.stdout.write(self.style.ERROR(f"Failed to send to {email}: {e}"))

                # Delay to prevent spam
                if delay > 0:
                    self.stdout.write(f"Waiting {delay} seconds...")
                    time.sleep(delay)
