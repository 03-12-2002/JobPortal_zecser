from django.contrib import admin
from .models import Job, Application

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company_name', 'employer', 'location', 'job_type', 'is_active', 'created_at')
    list_filter = ('is_active', 'job_type', 'created_at')
    search_fields = ('title', 'company_name', 'description')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'job', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('applicant__email', 'job__title')
    readonly_fields = ('applied_at', 'updated_at')