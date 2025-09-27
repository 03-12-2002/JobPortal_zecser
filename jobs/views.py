from rest_framework import generics, permissions, serializers
from rest_framework.parsers import MultiPartParser, JSONParser
from django.shortcuts import get_object_or_404
from .models import Job, Application
from .permissions import IsCompanyMemberOrReadOnly, IsAdminOfApplicationCompany
from .serializers import JobSerializer, JobDetailSerializer, ApplicationSerializer, EmployerApplicationSerializer, ApplicationStatusSerializer, EmployerJobSerializer
from accounts.models import EmployerProfile, User
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import PermissionDenied, ValidationError

class IsEmployer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'employer'

class IsJobOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.employer == request.user


class JobListCreateView(generics.ListCreateAPIView):
    
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):

        if (self.request.user.is_authenticated and 
            self.request.user.user_type == 'employer' and 
            hasattr(self.request.user, 'employer_profile') and
            hasattr(self.request.user.employer_profile, 'company') and
            self.request.user.employer_profile.company is not None):
            return EmployerJobSerializer
        return JobSerializer
    
    def get_queryset(self):
        queryset = Job.objects.filter(is_active=True)

        if self.request.user.user_type == 'employer' and hasattr(self.request.user, 'employer_profile'):
            try:
                if hasattr(self.request.user.employer_profile, 'company') and self.request.user.employer_profile.company:
                    employer_company = self.request.user.employer_profile.company

                    return Job.objects.filter(company=employer_company)
            except (EmployerProfile.DoesNotExist, AttributeError):
                pass
        return queryset
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        if self.request.user.user_type != User.EMPLOYER:
            raise PermissionDenied("Only employers can post jobs.")
        
        employer_profile = getattr(self.request.user, "employer_profile", None)
        if not employer_profile or not employer_profile.company:
            raise ValidationError("Employer must belong to a company to post jobs.")
        
        serializer.save(
            employer=self.request.user,
            company=employer_profile.company
        )
class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Job.objects.all()
    serializer_class = JobDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsCompanyMemberOrReadOnly]

    def perform_update(self, serializer):
        serializer.save()

class ApplicationCreateView(generics.CreateAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, JSONParser]

    def perform_create(self, serializer):
        job_id = self.kwargs.get('job_id')
        job = get_object_or_404(Job, id=job_id, is_active=True)

        if Application.objects.filter(job=job, applicant=self.request.user).exists():
            raise serializers.ValidationError("You have already applied for this job.")

        if self.request.user.user_type != 'jobseeker':
            raise serializers.ValidationError("Only job seekers can apply for jobs.")
        
        serializer.save(job=job, applicant=self.request.user)

class UserApplicationListView(generics.ListAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']

    def get_queryset(self):
        return Application.objects.filter(applicant=self.request.user)
    
# class UserApplicationListView(generics.ListAPIView):
#     serializer_class = ApplicationSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_queryset(self):
#         queryset = Application.objects.filter(applicant=self.request.user)
#         # Get the status from query parameters e.g., /my-applications/?status=accepted
#         status = self.request.query_params.get('status', None)
#         if status is not None:
#             # Filter the queryset by the provided status
#             queryset = queryset.filter(status=status)
#         return queryset

class EmployerApplicationListView(generics.ListAPIView):
    serializer_class = EmployerApplicationSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmployer]

    def get_queryset(self):
        employer_profile = get_object_or_404(EmployerProfile, user=self.request.user)

        if not employer_profile.company:
            return Application.objects.none()
           
        return Application.objects.filter(job__company=employer_profile.company)
    

class ApplicationStatusUpdateView(generics.UpdateAPIView):

    queryset = Application.objects.all()
    serializer_class = ApplicationStatusSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOfApplicationCompany]
    http_method_names = ['patch']

class EmployerJobListView(generics.ListAPIView):

    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not (self.request.user.user_type == 'employer' and hasattr(self.request.user, 'employer_profile')):
            return Job.objects.none()
        
        employer_company = self.request.user.employer_profile.company
        if not employer_company:
            return Job.objects.none()
            
        return Job.objects.filter(company=employer_company)