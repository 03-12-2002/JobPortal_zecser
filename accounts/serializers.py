from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from django.core.cache import cache
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class RequestOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=["register", "reset"])


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=["register", "reset"])
    otp = serializers.CharField(max_length=6)

class SignupSerializer(serializers.ModelSerializer):
    # extra fields
    password = serializers.CharField(write_only=True, min_length=6)
    verification_token = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "password", "verification_token")

    def validate(self, attrs):
        token = attrs.get("verification_token")
        email = attrs.get("email")

        # lookup token in cache
        cache_key = f"verified:register:{token}"
        cached_email = cache.get(cache_key)

        if not cached_email or cached_email != email:
            raise ValidationError({"verification_token": "Invalid or expired token."})

        return attrs

    def create(self, validated_data):
        validated_data.pop("verification_token")
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)

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
