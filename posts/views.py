from rest_framework import viewsets, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Post, PostLike, Comment
from .serializers import PostSerializer, CommentSerializer
from .permissions import IsAuthorOrReadOnly, IsCommentAuthorOrPostOwner, CanDeleteComment

class PostViewSet(viewsets.ModelViewSet):

    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    queryset = Post.objects.all().order_by('-created_at')

    def get_queryset(self):
        return Post.objects.all().order_by('-created_at')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uploaded_images = request.FILES.getlist('uploaded_images')
        post = serializer.save(author=request.user, uploaded_images=uploaded_images)
        output = PostSerializer(post, context={'request': request}).data
        headers = self.get_success_headers(output)
        return Response(output, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        uploaded_images = request.FILES.getlist('uploaded_images')
        remove_image_ids = request.data.get('remove_image_ids', None)

        # Always normalize into a list of ints
        if remove_image_ids:
            if isinstance(remove_image_ids, str):
                try:
                    import json
                    parsed = json.loads(remove_image_ids)
                    if isinstance(parsed, list):
                        remove_image_ids = parsed
                    else:
                        remove_image_ids = [int(parsed)]
                except Exception:
                    remove_image_ids = [int(r.strip()) for r in remove_image_ids.split(",") if r.strip().isdigit()]
            elif isinstance(remove_image_ids, int):
                remove_image_ids = [remove_image_ids]
        else:
            remove_image_ids = []

        serializer.save(uploaded_images=uploaded_images, remove_image_ids=remove_image_ids)

        # 🔑 Refresh so latest data is returned
        instance.refresh_from_db()
        return Response(PostSerializer(instance, context={'request': request}).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": "Your post deleted successfully"},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        user = request.user

        existing_like = PostLike.objects.filter(post=post, user=user).first()

        if existing_like:
            existing_like.delete()
            return Response(
                {"message": "Post unliked.", "likes_count": post.likes.count()},
                status=status.HTTP_200_OK
            )
        else:
            PostLike.objects.create(post=post, user=user)
            return Response(
                {"message": "Post liked.", "likes_count": post.likes.count()},
                status=status.HTTP_201_CREATED
            )
        
    @action(detail=True, methods=["get", "post"], permission_classes=[permissions.IsAuthenticated])
    def comments(self, request, pk=None):
        post = self.get_object()

        if request.method == "GET":
            comments = post.comments.all()
            serializer = CommentSerializer(comments, many=True, context={"request": request})
            return Response(serializer.data)

        if request.method == "POST":
            serializer = CommentSerializer(data=request.data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            serializer.save(author=request.user, post=post)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by("-created_at")
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, CanDeleteComment]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # The `CanDeleteComment` permission class already checked if the user is allowed.
        # We can just proceed with deletion.
        self.perform_destroy(instance)
        return Response(
            {"detail": "Comment deleted successfully."},
            status=status.HTTP_200_OK
        )