from rest_framework import serializers
from .models import JobSeekerProfile, EmployerProfile

class JobSeekerProfileSerializer(serializers.ModelSerializer):
    skills = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = JobSeekerProfile
        fields = [
            'resume', 'skills', 'education', 'experience',
            'expected_salary', 'preferred_location'
        ]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['skills'] = instance.skills.split(',') if instance.skills else []
        return rep

    def to_internal_value(self, data):
        if 'skills' in data and isinstance(data['skills'], list):
            data['skills'] = ','.join([s.strip() for s in data['skills'] if s.strip()])
        return super().to_internal_value(data)


class EmployerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployerProfile
        fields = [
            'company_name', 'company_description', 'company_website',
            'company_size', 'industry', 'company_logo'
        ]
