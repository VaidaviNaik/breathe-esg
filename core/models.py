from django.db import models
import uuid


class Client(models.Model):
    """Multi-tenancy: every row belongs to a client"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class IngestionBatch(models.Model):
    """Tracks each upload/ingestion event"""
    SOURCE_TYPES = [
        ('SAP', 'SAP Fuel & Procurement'),
        ('UTILITY', 'Utility Electricity'),
        ('TRAVEL', 'Corporate Travel'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_file_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    row_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.source_type} - {self.uploaded_at.date()}"


class EmissionRecord(models.Model):
    """
    Normalized emission record — the core fact table.
    All quantities are normalized to a standard unit before storing.
    """
    SCOPE_CHOICES = [
        (1, 'Scope 1 - Direct'),
        (2, 'Scope 2 - Electricity'),
        (3, 'Scope 3 - Value Chain'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('FLAGGED', 'Flagged / Suspicious'),
        ('REJECTED', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE)

    # Scope & Category
    scope = models.IntegerField(choices=SCOPE_CHOICES)
    category = models.CharField(max_length=100)

    # Activity data (normalized)
    activity_value = models.FloatField()
    activity_unit = models.CharField(max_length=50)
    activity_unit_original = models.CharField(max_length=50, blank=True)

    # Calculated emissions (tCO2e)
    co2e_kg = models.FloatField(null=True, blank=True)

    # Time & Location
    period_start = models.DateField()
    period_end = models.DateField()
    location = models.CharField(max_length=255, blank=True)

    # Source of truth tracking
    source_row_id = models.CharField(max_length=255, blank=True)
    raw_data = models.JSONField(default=dict)

    # Review
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reviewed_by = models.CharField(max_length=100, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    analyst_note = models.TextField(blank=True)

    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    edit_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.category} | {self.activity_value} {self.activity_unit} | {self.period_start}"


class ParseError(models.Model):
    """Tracks rows that failed to parse during ingestion"""
    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE)
    row_number = models.IntegerField()
    raw_row = models.JSONField(default=dict)
    error_message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
