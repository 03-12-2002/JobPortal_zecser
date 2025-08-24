from rest_framework import serializers
from .models import Job, Application
from accounts.profile_serializers import EmployerProfileSerializer

class JobSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='employer.company_name', read_only=True)
    
    class Meta:
        model = Job
        fields = [
            'id', 'employer', 'title', 'description', 'requirements', 
            'location', 'job_type', 'salary', 'company_name', 'is_active', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'employer', 'created_at', 'updated_at')

class JobDetailSerializer(JobSerializer):
    
    employer_details = EmployerProfileSerializer(source='employer', read_only=True)

    class Meta(JobSerializer.Meta):
        
        fields = JobSerializer.Meta.fields + ['employer_details']

class ApplicationSerializer(serializers.ModelSerializer):
    applicant_email = serializers.EmailField(source='applicant.email', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)

    job_id = serializers.UUIDField(source='job.id', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'job', 'job_id', 'applicant', 'applicant_email', 'job_title', 
            'cover_letter', 'status', 'applied_at', 'updated_at'
        ]
        read_only_fields = ('id', 'job', 'applicant', 'applied_at', 'updated_at')