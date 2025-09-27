

from rest_framework import generics, status, permissions, serializers
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Follow, User, CompanyProfile
from .follow_serializers import FollowSerializer


class FollowCreateView(generics.CreateAPIView):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()

class UnfollowView(generics.DestroyAPIView):

    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        user_to_unfollow_id = self.kwargs.get('user_id')
        company_to_unfollow_id = self.kwargs.get('company_id')
        follower = self.request.user

        if user_to_unfollow_id:
            following_user = get_object_or_404(User, id=user_to_unfollow_id)
            follow_instance = get_object_or_404(Follow, follower=follower, following_user=following_user)
        elif company_to_unfollow_id:
            following_company = get_object_or_404(CompanyProfile, id=company_to_unfollow_id)
            follow_instance = get_object_or_404(Follow, follower=follower, following_company=following_company)
        else:
            raise serializers.ValidationError("Must provide a user_id or company_id.")
        
        return follow_instance
    
    def delete(self, request, *args, **kwargs):
        follow_instance = self.get_object()
        follow_instance.delete()
        return Response({"detail": "Unfollowed successfully."}, status=status.HTTP_200_OK)
        