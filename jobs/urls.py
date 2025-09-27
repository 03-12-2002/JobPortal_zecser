from django.urls import path
from . import views
from .views import ApplicationStatusUpdateView, EmployerJobListView

urlpatterns = [
    path('', views.JobListCreateView.as_view(), name='job-list'),
    path('employer/my-jobs/', EmployerJobListView.as_view(), name='employer-my-jobs'),
    path('<int:pk>/', views.JobDetailView.as_view(), name='job-detail'),
    path('<int:job_id>/apply/', views.ApplicationCreateView.as_view(), name='apply-job'),
    path('my-applications/', views.UserApplicationListView.as_view(), name='my-applications'),
    path('employer/applications/', views.EmployerApplicationListView.as_view(), name='employer-applications'),
    path('employer/applications/<int:pk>/status/', ApplicationStatusUpdateView.as_view(), name='update-application-status'),
]