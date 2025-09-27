from rest_framework import serializers
from .models import JobSeekerProfile, EmployerProfile, CompanyProfile, Follow

class CompanyProfileSerializer(serializers.ModelSerializer):

    follower_count = serializers.SerializerMethodField(read_only=True)
    is_following = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = CompanyProfile
        fields = [
            'id', 'user','company_name', 'company_description', 'company_website',
            'company_size', 'industry', 'company_logo', 'headquarters_location',
            'is_approved', 'date_created',
            'follower_count', 'is_following'
        ]
        read_only_fields = ('id', 'is_approved', 'date_created')

    def get_follower_count(self, obj):
        return obj.followers.count()
    
    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(follower=request.user, following_company=obj).exists()
        return False

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
        data = data.copy() if isinstance(data, dict) else dict(data)

        if 'skills' in data:
            skills_val = data['skills']
            if isinstance(skills_val, str):
                data['skills'] = [s.strip() for s in skills_val.split(',') if s.strip()]

        return super().to_internal_value(data)

    def _join_skills(self, skills_list):
        return ','.join([s.strip() for s in skills_list if s and str(s).strip()])
    
    def create(self, validated_data):
        skills_list = validated_data.pop('skills', None)
        if skills_list is not None:
            validated_data['skills'] = self._join_skills(skills_list)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        skills_list = validated_data.pop('skills', None)
        if skills_list is not None:
            validated_data['skills'] = self._join_skills(skills_list)

        return super().update(instance, validated_data)


class EmployerProfileSerializer(serializers.ModelSerializer):
    company = CompanyProfileSerializer(read_only=True)
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=CompanyProfile.objects.all(),
        source='company',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = EmployerProfile
        fields = [
            'company', 'company_id', 'job_title', 'is_company_admin'
        ]

class CompanyCreateSerializer(serializers.ModelSerializer):
    make_me_admin = serializers.BooleanField(write_only=True, default=True, help_text="Make the requesting user a company admin.")
    class Meta:
        model = CompanyProfile
        fields = [
            'company_name', 'company_description', 'company_website',
            'company_size', 'industry', 'company_logo', 'headquarters_location',
            'make_me_admin'
        ]

    def create(self, validated_data):
        make_me_admin = validated_data.pop('make_me_admin', True)

        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication required to create a company.")
        
        if CompanyProfile.objects.filter(user=user).exists():
            raise serializers.ValidationError("You already have a company profile.")

        company = CompanyProfile.objects.create(user=user, **validated_data)

        try:
            employer_profile = user.employer_profile
        except EmployerProfile.DoesNotExist:
            employer_profile = EmployerProfile.objects.create(user=user)

        if make_me_admin:
            employer_profile.company = company
            employer_profile.is_company_admin = True
            employer_profile.save()

        return company

class CompanyUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = CompanyProfile
        fields = [
            'company_name', 'company_description', 'company_website',
            'company_size', 'industry', 'company_logo', 'headquarters_location'
        ]