from rest_framework import serializers
from .models import Job, Application
from accounts.profile_serializers import CompanyProfileSerializer
from accounts.serializers import UserProfileSerializer

class JobSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.company_name', read_only=True)

    class Meta:
        model = Job
        fields = [
            'id', 'company', 'title', 'description', 'requirements', 
            'location', 'job_type', 'salary', 'company_name', 'is_active', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'company', 'created_at', 'updated_at')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        request = self.context.get('request')
        
        if (
            request and 
            request.user.is_authenticated and
            hasattr(request.user, 'employer_profile') and
            getattr(request.user.employer_profile, 'company', None) and
            request.user.employer_profile.company.id == instance.company.id
        ):
            
            representation['application_count'] = instance.applications.count()
        
        return representation

class EmployerJobSerializer(JobSerializer):
    application_count = serializers.SerializerMethodField(read_only=True)

    class Meta(JobSerializer.Meta):
        fields = JobSerializer.Meta.fields + ['application_count']

    def get_application_count(self, obj):
        return obj.applications.count()
    
# class JobListCreateView(generics.ListCreateAPIView):
#     # Use different serializer based on user type
#     def get_serializer_class(self):
#         if (self.request.user.user_type == 'employer' and 
#             hasattr(self.request.user, 'employer_profile') and
#             self.request.user.employer_profile.company):
#             return EmployerJobSerializer
#         return JobSerializer

class JobDetailSerializer(JobSerializer):
    
    # employer_details = EmployerProfileSerializer(source='employer', read_only=True)
    company_details = CompanyProfileSerializer(source='company', read_only=True)

    class Meta(JobSerializer.Meta):
        fields = JobSerializer.Meta.fields + ['company_details']
class ApplicationSerializer(serializers.ModelSerializer):
    applicant_email = serializers.EmailField(source='applicant.email', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)

    job_id = serializers.IntegerField(source='job.id', read_only=True)
    resume = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Application
        fields = [
            'id', 'job', 'job_id', 'applicant', 'applicant_email', 'job_title', 
            'cover_letter', 'resume', 'status', 'applied_at', 'updated_at'
        ]
        read_only_fields = ('id', 'job', 'applicant', 'applied_at', 'updated_at', 'status')

class EmployerApplicationSerializer(serializers.ModelSerializer):
    applicant_details = UserProfileSerializer(source='applicant', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    job_id = serializers.IntegerField(source='job.id', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'job_id', 'job_title', 'applicant', 'applicant_details', 
            'cover_letter', 'resume', 'status', 'applied_at', 'updated_at'
        ]
        read_only_fields = fields

class ApplicationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['status']