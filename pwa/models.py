from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class SyncRecord(models.Model):
    """Track sync operations for offline/online data synchronization"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Sync details
    model_name = models.CharField(max_length=100, help_text="Model being synced")
    record_id = models.CharField(max_length=100, help_text="ID of the record being synced")
    operation = models.CharField(max_length=20, choices=[
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    ])
    
    # Sync status
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('CONFLICT', 'Conflict'),
    ], default='PENDING')
    
    # Data and metadata
    data = models.JSONField(help_text="Data to be synced")
    conflict_data = models.JSONField(null=True, blank=True, help_text="Server data in case of conflict")
    error_message = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    last_attempt = models.DateTimeField(null=True, blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    
    # Priority for sync queue
    priority = models.PositiveIntegerField(default=5, help_text="1=High, 5=Low")
    
    class Meta:
        ordering = ['priority', 'created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['model_name', 'record_id']),
            models.Index(fields=['priority', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.operation} {self.model_name} ({self.status})"


class OfflineSession(models.Model):
    """Track offline sessions for analytics and sync coordination"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Session details
    session_key = models.CharField(max_length=100, unique=True)
    device_info = models.JSONField(default=dict, help_text="Browser/device information")
    
    # Offline period
    offline_start = models.DateTimeField(auto_now_add=True)
    offline_end = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    
    # Activity during offline period
    forms_filled = models.PositiveIntegerField(default=0)
    pages_visited = models.PositiveIntegerField(default=0)
    actions_queued = models.PositiveIntegerField(default=0)
    
    # Sync summary
    sync_completed = models.BooleanField(default=False)
    sync_errors = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-offline_start']
    
    def __str__(self):
        return f"Offline session for {self.user or 'Anonymous'} ({self.offline_start})"


class PWAInstallation(models.Model):
    """Track PWA installations for analytics"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Installation details
    platform = models.CharField(max_length=50)  # Windows, Mac, Android, etc.
    browser = models.CharField(max_length=50)   # Chrome, Firefox, Safari, etc.
    device_type = models.CharField(max_length=20, choices=[
        ('DESKTOP', 'Desktop'),
        ('MOBILE', 'Mobile'),
        ('TABLET', 'Tablet'),
    ])
    
    # Installation event
    installed_at = models.DateTimeField(auto_now_add=True)
    install_source = models.CharField(max_length=50, choices=[
        ('BANNER', 'Install Banner'),
        ('MENU', 'Browser Menu'),
        ('MANUAL', 'Manual Install'),
    ])
    
    # Usage tracking
    last_used = models.DateTimeField(null=True, blank=True)
    times_opened = models.PositiveIntegerField(default=0)
    still_installed = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-installed_at']
        unique_together = ['user', 'platform', 'browser']
    
    def __str__(self):
        return f"PWA Install: {self.user or 'Anonymous'} on {self.platform}"
