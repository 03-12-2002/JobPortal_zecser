from django.urls import path
from . import views

urlpatterns = [
    path('', views.JobListCreateView.as_view(), name='job-list'),
    path('<uuid:pk>/', views.JobDetailView.as_view(), name='job-detail'),
    path('<uuid:job_id>/apply/', views.ApplicationCreateView.as_view(), name='apply-job'),
    path('my-applications/', views.UserApplicationListView.as_view(), name='my-applications'),
    path('employer/applications/', views.EmployerApplicationListView.as_view(), name='employer-applications'),
]