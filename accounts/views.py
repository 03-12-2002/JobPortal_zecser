from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.core.files.storage import default_storage
import uuid
import secrets
import string
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RequestOTPSerializer, VerifyOTPSerializer, SignupSerializer, LoginSerializer, ResetPasswordSerializer, UserProfileSerializer, FullProfileSerializer, ChangePasswordSerializer, UserListSerializer
from .profile_serializers import *
from .services import send_otp_email, verify_otp
from .models import User, CompanyProfile, Follow
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .permissions import IsCompanyAdmin, IsCompanyMember
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


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

class ResendOTPView(generics.GenericAPIView):
    serializer_class = RequestOTPSerializer
    throttle_scope = "resend_otp"
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data["email"]
        purpose = serializer.validated_data["purpose"]
        send_otp_email(email, purpose)

        return Response(
            {"detail": f"A new OTP has been sent to {email}. It is valid for 5 minutes."},
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
            token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
            cache_key = f"verified:{purpose}:{token}"
            cache.set(cache_key, email, 600)

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
    
class ProfileView(generics.RetrieveUpdateAPIView):
    """
    Handles fetching and updating the authenticated user's full profile.
    Supports multipart for file uploads (profile/cover/resume).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = FullProfileSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        """Handle profile picture, cover picture, resume uploads with JSON fields."""
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserPublicProfileView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        data = UserProfileSerializer(user, context={'request': request}).data

        if user.user_type == User.JOBSEEKER and hasattr(user, "jobseeker_profile"):
            data["profile"] = JobSeekerProfileSerializer(user.jobseeker_profile, context={'request': request}).data
        elif user.user_type == User.EMPLOYER and hasattr(user, "employer_profile"):
            data["profile"] = EmployerProfileSerializer(user.employer_profile, context={'request': request}).data

        return Response(data)
    
class UserFollowersListView(generics.ListAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        user_id = self.kwargs.get('id')
        user = get_object_or_404(User, id=user_id)
        return User.objects.filter(following__following_user=user).distinct()


    def get_serializer_context(self):
        return {'request': self.request}
    
class UserFollowingUsersListView(generics.ListAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs.get('id')
        user = get_object_or_404(User, id=user_id)
        return User.objects.filter(followers__follower=user).distinct()


    def get_serializer_context(self):
        return {'request': self.request}
    
class UserFollowingCompaniesListView(generics.ListAPIView):
    serializer_class = CompanyProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs.get('id')
        user = get_object_or_404(User, id=user_id)
        return CompanyProfile.objects.filter(followers__follower=user).distinct()


    def get_serializer_context(self):
        return {'request': self.request}

class CompanyViewSet(ModelViewSet):
    queryset = CompanyProfile.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CompanyCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CompanyUpdateSerializer
        return CompanyProfileSerializer
    
    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy', 'invite_member']:
            permission_classes = [permissions.IsAuthenticated, IsCompanyAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated] 
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        serializer.save()
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_staff or user.is_superuser:
            return CompanyProfile.objects.all()
        
        if user.user_type == user.EMPLOYER and hasattr(user, 'employer_profile'):
            if user.employer_profile.company:
                return CompanyProfile.objects.filter(id=user.employer_profile.company.id)
            return CompanyProfile.objects.none()

        return CompanyProfile.objects.filter(is_approved=True)
    def destroy(self, request, *args, **kwargs):
        company = self.get_object()
        company_name = company.company_name

        # Ensure only company admins can delete
        if not request.user.is_authenticated or not IsCompanyAdmin().has_object_permission(request, self, company):
            return Response(
                {"detail": "You are not allowed to delete this company."},
                status=status.HTTP_403_FORBIDDEN
            )

        self.perform_destroy(company)
        return Response(
            {"detail": f"Your Company '{company_name}' has been deleted successfully."},
            status=status.HTTP_200_OK
        )


    @action(detail=True, methods=['post'], permission_classes=[IsCompanyAdmin])
    def invite_member(self, request, pk=None):
        company = self.get_object()
        return Response({
            'detail': f'Invitation process initiated for company {company.company_name}. '
                     'A proper invitation system would be implemented here.'
        }, status=status.HTTP_200_OK)

class MyCompanyView(generics.RetrieveAPIView):

    serializer_class = CompanyProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        if not hasattr(self.request.user, 'employer_profile') or not self.request.user.employer_profile.company:
            raise serializers.ValidationError("You are not associated with any company.")
        return self.request.user.employer_profile.company
    
class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)
    
class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(is_superuser=False).exclude(id=self.request.user.id)

class LogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"error": "Refresh token is required."}, status=400)

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"message": "Successfully logged out."}, status=200)

        except Exception:
            return Response({"error": "Invalid token or already logged out."}, status=400)