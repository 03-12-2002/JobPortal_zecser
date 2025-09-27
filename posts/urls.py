from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet, CommentViewSet

router = DefaultRouter()
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'', PostViewSet, basename='post')

urlpatterns = [
    path('', include(router.urls)),
]
