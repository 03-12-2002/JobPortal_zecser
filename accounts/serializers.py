import json
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.core.cache import cache
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse
from .models import JobSeekerProfile, EmployerProfile, Follow, User
from .profile_serializers import JobSeekerProfileSerializer, EmployerProfileSerializer

User = get_user_model()

class RequestOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=["register", "reset"])

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=["register", "reset"])
    otp = serializers.CharField(max_length=6)

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    verification_token = serializers.CharField(write_only=True)

    phone_number = serializers.CharField(required=False, allow_blank=True)
    user_type = serializers.ChoiceField(choices=[("jobseeker", "Jobseeker"), ("employer", "Employer")], required=False)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "phone_number", "user_type", "password", "verification_token")

    def validate(self, attrs):
        token = attrs.get("verification_token")
        email = attrs.get("email")

        cache_key = f"verified:register:{token}"
        cached_email = cache.get(cache_key)

        if not cached_email or cached_email != email:
            raise ValidationError({"verification_token": "Invalid or expired token."})

        return attrs

    def create(self, validated_data):
        validated_data.pop("verification_token")
        password = validated_data.pop("password")
        
        user = User.objects.create_user(password=password, **validated_data)

        if user.user_type == User.JOBSEEKER:
            JobSeekerProfile.objects.create(user=user)
        elif user.user_type == User.EMPLOYER:
            
            EmployerProfile.objects.create(user=user)

        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        # ✅ now authenticate using email
        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password
        )

        if not user:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone_number": user.phone_number,
                "user_type": user.user_type,
            },
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    verification_token = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        email = attrs.get("email")
        token = attrs.get("verification_token")

        cache_key = f"verified:reset:{token}"
        cached_email = cache.get(cache_key)

        if not cached_email or cached_email != email:
            raise serializers.ValidationError({"verification_token": "Invalid or expired token."})

        return attrs

    def save(self, **kwargs):
        email = self.validated_data["email"]
        password = self.validated_data["new_password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "No user found with this email."})

        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    user_type_display = serializers.CharField(source="get_user_type_display", read_only=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    follower_count = serializers.SerializerMethodField(read_only=True)
    following_count = serializers.SerializerMethodField(read_only=True)
    is_following = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id", "email", "first_name", "last_name",
            "phone_number", "user_type", "user_type_display",
            "date_joined", "profile_picture", "cover_picture",
            "follower_count", "following_count", "is_following"
        )
        read_only_fields = ("id", "email", "date_joined", "user_type_display")

    def get_follower_count(self, obj):
        return Follow.objects.filter(following_user=obj).count()
        
    def get_following_count(self, obj):
        return Follow.objects.filter(follower=obj).count()
        
    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(follower=request.user, following_user=obj).exists()
        return False

class FullProfileSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    user_type_display = serializers.CharField(source="get_user_type_display", read_only=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    cover_picture = serializers.ImageField(required=False, allow_null=True)
    followers_count = serializers.SerializerMethodField(read_only=True)
    following_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name",
            "phone_number", "user_type", "user_type_display",
            "profile_picture", "cover_picture",
            "profile", "followers_count", "following_count"
        ]
        read_only_fields = ("id", "email", "date_joined", "user_type_display")

    def get_profile(self, obj):
        request = self.context.get("request")
        if obj.user_type == User.JOBSEEKER and hasattr(obj, "jobseeker_profile"):
            return JobSeekerProfileSerializer(obj.jobseeker_profile, context={"request": request}).data
        elif obj.user_type == User.EMPLOYER and hasattr(obj, "employer_profile"):
            return EmployerProfileSerializer(obj.employer_profile, context={"request": request}).data
        return None

    def get_followers_count(self, obj):
        return Follow.objects.filter(following_user=obj).count()

    def get_following_count(self, obj):
        return Follow.objects.filter(follower=obj).count()

    def update(self, instance, validated_data):
        request = self.context.get("request")
        profile_data = {}
        incoming_profile = request.data.get("profile", None)

        # 1) If request includes top-level profile JSON string -> parse it
        if isinstance(incoming_profile, dict):
            profile_data = incoming_profile.copy()
        else:
            if incoming_profile:
                try:
                    profile_data = json.loads(incoming_profile)
                except Exception:
                    profile_data = {}

            # 2) Collect individual profile.* form fields
            for key, value in request.data.items():
                if key.startswith("profile."):
                    sub_key = key.split("profile.", 1)[1]
                    profile_data[sub_key] = value

        # 3) Collect files: both profile.* files and top-level file fields
        if hasattr(request, "FILES") and request.FILES:
            for fkey, fval in request.FILES.items():
                if fkey.startswith("profile."):
                    sub_key = fkey.split("profile.", 1)[1]
                    profile_data[sub_key] = fval
                else:
                    # top-level files such as profile_picture, cover_picture
                    profile_data[fkey] = fval

        # 4) Try to parse JSON-stringified nested values (e.g. arrays sent from frontend as JSON strings)
        for k, v in list(profile_data.items()):
            if isinstance(v, str):
                v_strip = v.strip()
                if (v_strip.startswith("{") and v_strip.endswith("}")) or (v_strip.startswith("[") and v_strip.endswith("]")):
                    try:
                        profile_data[k] = json.loads(v_strip)
                    except Exception:
                        # leave as string if JSON parse fails
                        profile_data[k] = v

        # 5) Normalize skills: if it's a comma-separated string -> convert to list; if already list, keep it
        if "skills" in profile_data:
            skills_val = profile_data["skills"]
            if isinstance(skills_val, str):
                # comma separated string
                profile_data["skills"] = [s.strip() for s in skills_val.split(",") if s.strip()]
            elif isinstance(skills_val, (list, tuple)):
                profile_data["skills"] = list(skills_val)

        # 6) Apply top-level file fields to the User instance before nested serializer
        if "profile_picture" in profile_data and profile_data["profile_picture"] is not None:
            instance.profile_picture = profile_data.pop("profile_picture")
        if "cover_picture" in profile_data and profile_data["cover_picture"] is not None:
            instance.cover_picture = profile_data.pop("cover_picture")

        # 7) Update basic user fields from validated_data
        basic_fields = ["first_name", "last_name", "phone_number", "profile_picture", "cover_picture"]
        for field in basic_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()

        # 8) Update nested jobseeker/employer profiles using their serializers (partial update)
        if instance.user_type == User.JOBSEEKER and hasattr(instance, "jobseeker_profile"):
            profile_serializer = JobSeekerProfileSerializer(
                instance.jobseeker_profile,
                data=profile_data,
                partial=True,
                context=self.context
            )
            profile_serializer.is_valid(raise_exception=True)
            profile_serializer.save()

        elif instance.user_type == User.EMPLOYER and hasattr(instance, "employer_profile"):
            profile_serializer = EmployerProfileSerializer(
                instance.employer_profile,
                data=profile_data,
                partial=True,
                context=self.context
            )
            profile_serializer.is_valid(raise_exception=True)
            profile_serializer.save()

        return instance
    
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=6)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Your old password was entered incorrectly.")
        return value
    
    def save(self, **kwargs):
        user = self.context['request'].user
        password = self.validated_data['new_password']
        user.set_password(password)
        user.save()
        return user


class UserListSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'user_name', 'user_type', 'followers_count', 'following_count']

    def get_user_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_followers_count(self, obj):
        return Follow.objects.filter(following_user=obj).count()

    def get_following_count(self, obj):
        return Follow.objects.filter(follower=obj).count()
    