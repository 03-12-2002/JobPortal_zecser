from rest_framework import serializers
from .models import Post, PostImage, Comment

class PostImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)
    class Meta:
        model = PostImage
        fields = ['id', 'image']

class PostSerializer(serializers.ModelSerializer):

    images = PostImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )
    remove_image_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    author_email = serializers.EmailField(source='author.email', read_only=True)
    author = serializers.PrimaryKeyRelatedField(read_only=True)

    likes_count = serializers.SerializerMethodField(read_only=True)
    is_liked = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'author_email', 'content',
            'images', 'uploaded_images', 'remove_image_ids',
            'created_at', 'updated_at',
            'likes_count', 'is_liked'
        ]

        read_only_fields = ['id', 'author', 'created_at', 'updated_at', 'likes_count', 'is_liked']

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        post = Post.objects.create(**validated_data)
        for image in uploaded_images:
            PostImage.objects.create(post=post, image=image)
        return post
    
    def update(self, instance, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        remove_image_ids = validated_data.pop('remove_image_ids', [])

        # Ensure integers
        remove_image_ids = [int(r) for r in remove_image_ids if str(r).isdigit()]

        # Update content
        instance.content = validated_data.get('content', instance.content)
        instance.save()

        # Remove images properly
        if remove_image_ids:
            for img in PostImage.objects.filter(id__in=remove_image_ids, post=instance):
                img.image.delete(save=False)  # remove file from disk
                img.delete()

        # Add new images
        for image in uploaded_images:
            PostImage.objects.create(post=instance, image=image)

        return instance




class CommentSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source="author.email", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "post", "author", "author_email", "content", "created_at", "updated_at"]
        read_only_fields = ["id", "author", "author_email", "created_at", "updated_at", "post"]
