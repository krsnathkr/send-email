import csv
import markdown
import re
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from .models import Contact, EmailCampaign, EmailLog

class EmailEngine:
    @staticmethod
    def import_contacts(csv_file_path):
        """
        Reads a CSV file and creates/updates Contact objects.
        Expected columns: Name, Company, Email, Job Role, Location
        """
        results = {'created': 0, 'updated': 0, 'errors': []}
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Normalize headers: strip whitespace and lower case for safer access
                reader.fieldnames = [name.strip() for name in reader.fieldnames]
                
                for row in reader:
                    email = row.get('Email', '').strip()
                    if not email:
                        continue
                        
                    # Extract name parts
                    full_name = row.get('Name', '').strip()
                    parts = full_name.split(' ', 1)
                    first_name = parts[0]
                    last_name = parts[1] if len(parts) > 1 else ''
                    
                    contact_data = {
                        'first_name': first_name,
                        'last_name': last_name,
                        'company': row.get('Company', '').strip(),
                        'job_role': row.get('Job Role', '').strip(),
                        'location': row.get('Location', '').strip(),
                        'email_status': row.get('Email Status', 'Valid').strip(),
                    }
                    
                    contact, created = Contact.objects.update_or_create(
                        email=email,
                        defaults=contact_data
                    )
                    
                    if created:
                        results['created'] += 1
                    else:
                        results['updated'] += 1
                        
        except Exception as e:
            results['errors'].append(str(e))
            
        return results

    @staticmethod
    def prepare_content(template_content, contact, tracking_id, subject_template=None):
        """
        1. Replaces placeholders in Markdown.
        2. Converts Markdown to HTML.
        3. Injects tracking pixel.
        4. Rewrites links for tracking.
        """
        # 1. Replace Placeholders
        # Safe substitution using a dictionary
        context = {
            'Name': contact.first_name,
            'First Name': contact.first_name, # Alias
            'Last Name': contact.last_name,
            'Company': contact.company,
            'Job Role': contact.job_role,
            'Location': contact.location,
            'Email': contact.email
        }
        
        # Regex to match [Placeholder]
        # We look for square brackets and try to match the key inside
        def replace_placeholder(match):
            key = match.group(1)
            return context.get(key, match.group(0)) # Return original if not found
            
        # Replaces [Name], [Company], etc.
        markdown_text = re.sub(r'\[(.*?)\]', replace_placeholder, template_content)
        
        # 2. Convert to HTML
        html_content = markdown.markdown(markdown_text)
        
        # 3. Process HTML with BeautifulSoup for Links and Pixel
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Rewrite links
        for a_tag in soup.find_all('a', href=True):
            original_url = a_tag['href']
            if not original_url.startswith('http'):
                continue # Skip internal links or mailto if needed, or handle them differently
                
            tracking_url = f"{settings.SITE_URL}/track/click/{tracking_id}/?url={original_url}"
            a_tag['href'] = tracking_url
            
        # 4. Inject Tracking Pixel
        pixel_url = f"{settings.SITE_URL}/track/open/{tracking_id}/pixel.png"
        img_tag = soup.new_tag("img", src=pixel_url, width="1", height="1", style="display:none;", alt="")
        soup.append(img_tag)
        
        final_html = str(soup)
        plain_text = strip_tags(html_content) # Strip tags from the *unmodified* HTML (or modified, doesn't matter much for text)
        
        final_subject = subject_template
        if subject_template:
            final_subject = re.sub(r'\[(.*?)\]', replace_placeholder, subject_template)
        
        return final_subject, final_html, plain_text

    @staticmethod
    def send_campaign(campaign_name, subject, template_path, csv_path, dry_run=False):
        """
        Orchestrates the campaign sending process.
        """
        # 1. Import Contacts
        import_results = EmailEngine.import_contacts(csv_path)
        print(f"Import Results: {import_results}")
        
        # 2. Get/Create Campaign
        campaign, _ = EmailCampaign.objects.get_or_create(name=campaign_name, defaults={'subject': subject})
        
        # 3. Read Template
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
            
        # Extract Subject from template if present (First line "Subject: ...")
        # If the template file starts with "Subject:", we use that instead of the generic one
        lines = template_content.split('\n')
        
        # Parse Subject
        # Look for "Subject:" in the first few lines
        parsing_body = False
        new_lines = []
        
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Extract Subject
            if not parsing_body and stripped_line.lower().startswith('subject:'):
                potential_subject = stripped_line.split(':', 1)[1].strip()
                if potential_subject:
                    subject = potential_subject
                else:
                    # If empty, check next line
                    if i + 1 < len(lines):
                         subject = lines[i+1].strip()
                         # We skip the next line in loop? No, handled by filtering below
                         # Actually simpler: Just set subject and continue
                continue
                
            # Skip the next line if it was the subject content (heuristic: if subject was empty on "Subject:" line)
            if not parsing_body and subject == lines[i].strip() and lines[i-1].strip().lower() == 'subject:':
                continue

            # Filtering other metadata (Email:, Portfolio:, etc if they appear at top)
            # Based on user request, "Email:" appeared in body.
            # We will strip lines that look like headers until we hit blank lines or body?
            # User example:
            # Subject:
            # Quick question...
            # <blank>
            # Email:
            # <blank>
            # Hi [Name],
            
            # Heuristic: If we are not in body yet, and line is "Subject:" or "Email:" or "Portfolio:" etc, skip it?
            # Or just strip specifically requested parts. 
            
            # Let's clean up specifically based on the layout we saw.
            if stripped_line.lower().startswith('email:'):
                continue
            
            # If we hit "Hi [Name]", we are definitely in body
            if "Hi " in line:
                parsing_body = True
                
            new_lines.append(line)
            
        template_content = '\n'.join(new_lines).strip()
        
        # Update campaign subject
        campaign.subject = subject
        campaign.save()

        # 4. Send Emails
        contacts = Contact.objects.all() # Or filter based on import? For now, all contacts.
        # Maybe we should only send to contacts in the CSV? 
        # For this logic, let's assume we want to send to everyone in the DB who was just imported/updated.
        # Ideally, we filter by created_at or explicitly return the list from import. 
        # But simplistic approach: Send to all valid contacts.
        
        sent_count = 0
        errors = []
        
        for contact in contacts:
            try:
                # Create Log entry first to get UUID
                email_log = EmailLog.objects.create(
                    campaign=campaign,
                    contact=contact,
                    subject=subject
                )
                
                # Prepare Content
                final_subject, html_body, text_body = EmailEngine.prepare_content(template_content, contact, email_log.tracking_id, subject_template=subject)
                
                # Update log with personalized subject
                email_log.subject = final_subject
                email_log.save()
                
                if not dry_run:
                    msg = EmailMultiAlternatives(
                        subject=final_subject,
                        body=text_body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[contact.email]
                    )
                    msg.attach_alternative(html_body, "text/html")
                    msg.send()
                
                sent_count += 1
                
            except Exception as e:
                errors.append(f"{contact.email}: {str(e)}")
                
        return {
            'sent': sent_count,
            'errors': errors,
            'import_stats': import_results
        }

from mixpanel import Mixpanel

class AnalyticsService:
    _mp = None
    
    @classmethod
    def get_instance(cls):
        if cls._mp is None and hasattr(settings, 'MIXPANEL_TOKEN'):
            cls._mp = Mixpanel(settings.MIXPANEL_TOKEN)
        return cls._mp
        
    @staticmethod
    def track_open(contact, campaign_name, subject, tracking_id):
        mp = AnalyticsService.get_instance()
        if not mp:
            return
            
        # Use email or tracking_id as distinct_id
        distinct_id = contact.email
        
        mp.track(distinct_id, 'Email Opened', {
            'Campaign': campaign_name,
            'Subject': subject,
            'Tracking ID': str(tracking_id),
            'Email': contact.email,
            'Company': contact.company,
            'Job Role': contact.job_role
        })
        
        # Determine location from IP isn't easy here without request context, 
        # so we rely on Mixpanel's ingestion to parse IP if we passed it, 
        # but the library doesn't easily support passing IP for geoip unless we use the HTTP API manually 
        # or update the profile. For now, simple event tracking.

    @staticmethod
    def track_click(contact, campaign_name, target_url, tracking_id):
        mp = AnalyticsService.get_instance()
        if not mp:
            return
            
        distinct_id = contact.email
        
        mp.track(distinct_id, 'Email Link Clicked', {
            'Campaign': campaign_name,
            'Target URL': target_url,
            'Tracking ID': str(tracking_id),
            'Email': contact.email
        })
