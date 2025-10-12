from rest_framework import serializers
from .models import JobSeekerProfile, EmployerProfile, CompanyProfile, Follow, Skill, Education, Experience

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

class SkillSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Skill
        fields = ['id', 'name']
        read_only_fields = ['id']

class EducationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Education
        fields = ['id', 'degree', 'institution', 'period', 'created_at']
        read_only_fields = ['id', 'created_at']

class ExperienceSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Experience
        fields = ['id', 'title', 'company', 'description', 'period', 'start_date', 'end_date', 'is_current', 'created_at']
        read_only_fields = ['id', 'created_at']

class JobSeekerProfileSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)
    skills_input = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    educations = EducationSerializer(many=True, required=False)
    experiences = ExperienceSerializer(many=True, required=False)
    resume = serializers.FileField(required=False, allow_null=True)
    location = serializers.CharField(required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = JobSeekerProfile
        fields = [
            'resume', 'skills', 'skills_input', 'educations', 'experiences',
            'location', 'bio'
        ]
        read_only_fields = ('skills',)
    
    def _get_or_create_skill(self, name):
        name = str(name).strip()
        if not name:
            return None
        # case-insensitive get_or_create
        skill = Skill.objects.filter(name__iexact=name).first()
        if not skill:
            skill = Skill.objects.create(name=name)
        else:
            # normalize stored name (optional)
            if skill.name != name:
                skill.name = name
                skill.save()
        return skill

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # skills (read-only nested) are already handled by SkillSerializer
        # Ensure educations and experiences serialized correctly
        rep['educations'] = EducationSerializer(instance.educations.all(), many=True).data
        rep['experiences'] = ExperienceSerializer(instance.experiences.all(), many=True).data
        # Ensure skills shown as list of strings for convenience
        rep['skills'] = [s.name for s in instance.skills.all()]
        return rep
    
    def _sync_skills(self, profile, skills_input):
        """
        Accepts skills_input as list of strings (already normalized).
        Syncs profile.skills M2M to match provided list.
        """
        if skills_input is None:
            return

        # Allow comma-separated single string accidentally passed here (defensive)
        if isinstance(skills_input, str):
            skill_names = [s.strip() for s in skills_input.split(',') if s.strip()]
        elif isinstance(skills_input, (list, tuple)):
            skill_names = []
            for item in skills_input:
                if isinstance(item, dict):
                    nm = item.get('name', '').strip()
                else:
                    nm = str(item).strip()
                if nm:
                    skill_names.append(nm)
        else:
            return

        skill_objs = []
        for name in skill_names:
            skill = Skill.objects.filter(name__iexact=name).first()
            if not skill:
                skill = Skill.objects.create(name=name)
            skill_objs.append(skill)
        profile.skills.set(skill_objs)

    def _sync_educations(self, profile, educations_input):
        """
        Sync educations: update existing by id, create new ones; remove omitted ones.
        """
        if educations_input is None:
            return

        # incoming ids
        incoming_ids = [int(item.get('id')) for item in educations_input if isinstance(item, dict) and item.get('id')]

        # delete those not present
        existing_ids = [e.id for e in profile.educations.all()]
        to_delete = [eid for eid in existing_ids if eid not in incoming_ids]
        if to_delete:
            profile.educations.filter(id__in=to_delete).delete()

        # update/create
        for item in educations_input:
            if not isinstance(item, dict):
                continue
            eid = item.get('id', None)
            if eid:
                try:
                    edu = profile.educations.get(id=eid)
                    edu.degree = item.get('degree', edu.degree)
                    edu.institution = item.get('institution', edu.institution)
                    edu.period = item.get('period', edu.period)
                    edu.save()
                except Education.DoesNotExist:
                    Education.objects.create(
                        profile=profile,
                        degree=item.get('degree', ''),
                        institution=item.get('institution', ''),
                        period=item.get('period', '')
                    )
            else:
                Education.objects.create(
                    profile=profile,
                    degree=item.get('degree', ''),
                    institution=item.get('institution', ''),
                    period=item.get('period', '')
                )

    def _sync_experiences(self, profile, experiences_input):
        """
        Sync experiences similar to educations.
        """
        if experiences_input is None:
            return

        incoming_ids = [int(item.get('id')) for item in experiences_input if isinstance(item, dict) and item.get('id')]

        existing_ids = [e.id for e in profile.experiences.all()]
        to_delete = [eid for eid in existing_ids if eid not in incoming_ids]
        if to_delete:
            profile.experiences.filter(id__in=to_delete).delete()

        for item in experiences_input:
            if not isinstance(item, dict):
                continue
            eid = item.get('id', None)
            if eid:
                try:
                    exp = profile.experiences.get(id=eid)
                    exp.title = item.get('title', exp.title)
                    exp.company = item.get('company', exp.company)
                    exp.description = item.get('description', exp.description)
                    exp.period = item.get('period', exp.period)
                    if 'start_date' in item:
                        exp.start_date = item.get('start_date')
                    if 'end_date' in item:
                        exp.end_date = item.get('end_date')
                    if 'is_current' in item:
                        exp.is_current = bool(item.get('is_current'))
                    exp.save()
                except Experience.DoesNotExist:
                    Experience.objects.create(
                        profile=profile,
                        title=item.get('title', ''),
                        company=item.get('company', ''),
                        description=item.get('description', ''),
                        period=item.get('period', ''),
                        start_date=item.get('start_date', None),
                        end_date=item.get('end_date', None),
                        is_current=bool(item.get('is_current', False))
                    )
            else:
                Experience.objects.create(
                    profile=profile,
                    title=item.get('title', ''),
                    company=item.get('company', ''),
                    description=item.get('description', ''),
                    period=item.get('period', ''),
                    start_date=item.get('start_date', None),
                    end_date=item.get('end_date', None),
                    is_current=bool(item.get('is_current', False))
                )
    
    def create(self, validated_data):
        # Because JobSeekerProfile is created when user is created, create isn't typically used here
        # But implement for completeness
        skills_input = validated_data.pop('skills_input', None)
        educations_input = validated_data.pop('educations', None)
        experiences_input = validated_data.pop('experiences', None)

        profile = super().create(validated_data)

        self._sync_skills(profile, skills_input)
        self._sync_educations(profile, educations_input)
        self._sync_experiences(profile, experiences_input)

        return profile

    def update(self, instance, validated_data):
        skills_input = validated_data.pop('skills_input', None)
        educations_input = validated_data.pop('educations', None)
        experiences_input = validated_data.pop('experiences', None)

        # Update scalar fields
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        # Sync lists if provided
        self._sync_skills(instance, skills_input)
        self._sync_educations(instance, educations_input)
        self._sync_experiences(instance, experiences_input)

        return instance

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