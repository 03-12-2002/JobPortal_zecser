from rest_framework import serializers
from .models import Follow, User, CompanyProfile

class FollowSerializer(serializers.ModelSerializer):
    follower_email = serializers.CharField(source='follower.email', read_only=True)
    following_object = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'follower_email', 'following_user', 'following_company', 'following_object', 'created_at']
        read_only_fields = ('id', 'follower', 'created_at', 'follower_email', 'following_object')


    def get_following_object(self, obj):
        if obj.following_user:
            return f"User: {obj.following_user.email}"
        elif obj.following_company:
            return f"Company: {obj.following_company.company_name}"
        return None


    def validate(self, attrs):
        following_user = attrs.get('following_user')
        following_company = attrs.get('following_company')

        if not (following_user or following_company):
            raise serializers.ValidationError("You must specify either a user or a company to follow.")
        if following_user and following_company:
            raise serializers.ValidationError("You cannot follow both a user and a company in the same request.")
        
        request = self.context.get('request')
        if request and following_user and (following_user == request.user):
            raise serializers.ValidationError("You cannot follow yourself.")

        if request:
            follower = request.user
            if following_user and Follow.objects.filter(follower=follower, following_user=following_user).exists():
                raise serializers.ValidationError({"detail": "You are already following this user."})
            if following_company and Follow.objects.filter(follower=follower, following_company=following_company).exists():
                raise serializers.ValidationError({"detail": "You are already following this company."})
        return attrs


    def create(self, validated_data):
        validated_data['follower'] = self.context['request'].user
        return super().create(validated_data)