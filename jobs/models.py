import uuid
from django.db import models
from django.conf import settings
from accounts.models import EmployerProfile

class Job(models.Model):
    JOB_TYPE_FULL_TIME = 'full_time'
    JOB_TYPE_PART_TIME = 'part_time'
    JOB_TYPE_CONTRACT = 'contract'
    JOB_TYPE_INTERNSHIP = 'internship'
    JOB_TYPE_REMOTE = 'remote'

    JOB_TYPE_CHOICES = [
        (JOB_TYPE_FULL_TIME, 'Full Time'),
        (JOB_TYPE_PART_TIME, 'Part Time'),
        (JOB_TYPE_CONTRACT, 'Contract'),
        (JOB_TYPE_INTERNSHIP, 'Internship'),
        (JOB_TYPE_REMOTE, 'Remote'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, related_name="jobs")
    title = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField()
    location = models.CharField(max_length=255)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default=JOB_TYPE_FULL_TIME)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    company_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} at {self.company_name}"

class Application(models.Model):
    APPLICATION_STATUS_SUBMITTED = 'submitted'
    APPLICATION_STATUS_REVIEWED = 'reviewed'
    APPLICATION_STATUS_ACCEPTED = 'accepted'
    APPLICATION_STATUS_REJECTED = 'rejected'

    APPLICATION_STATUS_CHOICES = [
        (APPLICATION_STATUS_SUBMITTED, 'Submitted'),
        (APPLICATION_STATUS_REVIEWED, 'Reviewed'),
        (APPLICATION_STATUS_ACCEPTED, 'Accepted'),
        (APPLICATION_STATUS_REJECTED, 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications")
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS_CHOICES, default=APPLICATION_STATUS_SUBMITTED)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['job', 'applicant']
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.applicant.email} applied for {self.job.title}"