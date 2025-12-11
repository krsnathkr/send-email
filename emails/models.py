from django.db import models
from django.utils import timezone
import uuid

class Contact(models.Model):
    """Store your email contacts"""
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    company = models.CharField(max_length=200, blank=True)
    
    # Flexible field to store extra CSV columns as JSON
    extra_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.email
    
    class Meta:
        ordering = ['-created_at']


class EmailCampaign(models.Model):
    """Track different email campaigns"""
    name = models.CharField(max_length=200)
    subject = models.CharField(max_length=300)
    template_path = models.CharField(max_length=500, help_text="Path to the template file")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']


class EmailLog(models.Model):
    """Log each email sent (NO TRACKING)"""
    # UUID just for unique identification of this log entry, not for tracking
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE, related_name='emails')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    
    subject = models.CharField(max_length=300)
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='sent', choices=[('sent', 'Sent'), ('failed', 'Failed')])
    error_message = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.contact.email} - {self.subject}"
    
    class Meta:
        ordering = ['-sent_at']
