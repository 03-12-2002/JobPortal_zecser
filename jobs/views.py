from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Job, Application
from .permissions import IsJobOwnerOrReadOnly
from .serializers import JobSerializer, JobDetailSerializer, ApplicationSerializer
from accounts.models import EmployerProfile

class IsEmployer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'employer'

class IsJobOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.employer.user == request.user


class JobListCreateView(generics.ListCreateAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.user_type == 'employer':
            employer_profile = get_object_or_404(EmployerProfile, user=self.request.user)
            return Job.objects.filter(employer=employer_profile)
        else:
            return Job.objects.filter(is_active=True)

    def perform_create(self, serializer):
        employer_profile = get_object_or_404(EmployerProfile, user=self.request.user)
        serializer.save(employer=employer_profile, company_name=employer_profile.company_name)

class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Job.objects.all()
    serializer_class = JobDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsJobOwnerOrReadOnly]

    def perform_update(self, serializer):
        serializer.save()

class ApplicationCreateView(generics.CreateAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        job_id = self.kwargs.get('job_id')
        job = get_object_or_404(Job, id=job_id, is_active=True)
        if Application.objects.filter(job=job, applicant=self.request.user).exists():
            raise serializers.ValidationError("You have already applied for this job.")
        serializer.save(job=job, applicant=self.request.user)

class UserApplicationListView(generics.ListAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Application.objects.filter(applicant=self.request.user)

class EmployerApplicationListView(generics.ListAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmployer]

    def get_queryset(self):
        employer_profile = get_object_or_404(EmployerProfile, user=self.request.user)
        return Application.objects.filter(job__employer=employer_profile)