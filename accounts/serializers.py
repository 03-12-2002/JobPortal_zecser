from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from django.core.cache import cache
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse
from .models import JobSeekerProfile, EmployerProfile
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
    user_type = serializers.ChoiceField(choices=[("candidate", "Candidate"), ("employer", "Employer")], required=False)

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

        # auto-create profile
        if user.user_type == User.CANDIDATE:
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

        user = authenticate(request=self.context.get("request"), email=email, password=password)
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
            "profile_url": reverse("profile"),
            "public_profile_url": reverse("user-profile-detail", kwargs={"id": user.id}),
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

    class Meta:
        model = User
        fields = (
            "id", "email", "first_name", "last_name",
            "phone_number", "user_type", "user_type_display",
            "date_joined", "profile_picture"
        )
        read_only_fields = ("id", "email", "date_joined", "user_type_display")

class FullProfileSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    user_type_display = serializers.CharField(source="get_user_type_display", read_only=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            "id", "email", "first_name", "last_name", "phone_number",
            "user_type", "user_type_display", "profile_picture", "date_joined",
            "profile"
        )
        read_only_fields = ("id", "email", "date_joined", "user_type_display")

    def get_profile(self, obj):
        if obj.user_type == User.CANDIDATE and hasattr(obj, "jobseeker_profile"):
            return JobSeekerProfileSerializer(obj.jobseeker_profile).data
        elif obj.user_type == User.EMPLOYER and hasattr(obj, "employer_profile"):
            return EmployerProfileSerializer(obj.employer_profile).data
        return {}

    def update(self, instance, validated_data):
        basic_fields = ["first_name", "last_name", "phone_number", "profile_picture"]
        for field in basic_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()

        request = self.context.get("request")
        profile_data = request.data.get("profile", {})
        if instance.user_type == User.CANDIDATE and hasattr(instance, "jobseeker_profile"):
            serializer = JobSeekerProfileSerializer(instance.jobseeker_profile, data=profile_data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        elif instance.user_type == User.EMPLOYER and hasattr(instance, "employer_profile"):
            serializer = EmployerProfileSerializer(instance.employer_profile, data=profile_data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return instance
