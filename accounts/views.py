from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.core.files.storage import default_storage
import uuid
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RequestOTPSerializer, VerifyOTPSerializer, SignupSerializer, LoginSerializer, ResetPasswordSerializer, UserProfileSerializer, FullProfileSerializer
from .profile_serializers import *
from .services import send_otp_email, verify_otp
from .models import User
from django.contrib.auth import get_user_model

User = get_user_model()
class RequestOTPView(generics.GenericAPIView):
    serializer_class = RequestOTPSerializer
    throttle_scope = "otp"  

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        purpose = serializer.validated_data["purpose"]

        send_otp_email(email, purpose)

        return Response(
            {"detail": f"OTP has been sent to {email}. It is valid for 5 minutes."},
            status=status.HTTP_200_OK,
        )


class VerifyOTPView(generics.GenericAPIView):
    serializer_class = VerifyOTPSerializer
    throttle_scope = "verify"

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]
        purpose = serializer.validated_data["purpose"]

        if verify_otp(email, otp, purpose):
            # generate short-lived token (UUID stored in cache)
            token = str(uuid.uuid4())
            cache_key = f"verified:{purpose}:{token}"
            cache.set(cache_key, email, 600)  # valid 10 min

            return Response(
                {
                    "detail": "OTP verified successfully.",
                    "verification_token": token,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"detail": "Invalid or expired OTP."},
            status=status.HTTP_400_BAD_REQUEST,
        )

class SignupView(generics.GenericAPIView):
    serializer_class = SignupSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        data = {
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

            "next": reverse("profile"),
        }
        return Response(data, status=status.HTTP_201_CREATED)
    
class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        tokens = serializer.save()
        return Response(tokens, status=status.HTTP_200_OK)

class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password has been reset successfully."}, status=status.HTTP_200_OK)
    
from rest_framework.permissions import IsAuthenticated
from .profile_serializers import JobSeekerProfileSerializer, EmployerProfileSerializer
from rest_framework import generics
from .models import User
from .serializers import UserProfileSerializer


class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FullProfileSerializer

    # def get_serializer_class(self):
    #     if self.request.user.user_type == User.CANDIDATE:
    #         return JobSeekerProfileSerializer
    #     return EmployerProfileSerializer

    # def get_object(self):
    #     if self.request.user.user_type == User.CANDIDATE:
    #         return self.request.user.jobseeker_profile
    #     return self.request.user.employer_profile

    def get_object(self):
        return self.request.user


class UserPublicProfileView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        data = UserProfileSerializer(user).data

        if user.user_type == User.CANDIDATE and hasattr(user, "jobseeker_profile"):
            data["profile"] = JobSeekerProfileSerializer(user.jobseeker_profile).data
        elif user.user_type == User.EMPLOYER and hasattr(user, "employer_profile"):
            data["profile"] = EmployerProfileSerializer(user.employer_profile).data

        return Response(data)
