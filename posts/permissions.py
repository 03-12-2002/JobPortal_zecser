from rest_framework import permissions

class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow the author of a post to edit or delete it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the author of the post.
        return obj.author == request.user
    
class IsCommentAuthorOrPostOwner(permissions.BasePermission):
    """
    Only comment author can update. 
    Post owner can delete any comment on their post.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.method in ["PUT", "PATCH"]:
            return obj.author == request.user
        if request.method == "DELETE":
            return obj.author == request.user or obj.post.author == request.user
        return False

class CanDeleteComment(permissions.BasePermission):
    """
    Permission to only allow the author of a comment or the owner of the post to delete it.
    """
    def has_object_permission(self, request, view, obj):
        # Safe methods (GET, HEAD, OPTIONS) are always allowed
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # For DELETE requests: allow if user is the comment author OR the post author
        if request.method == "DELETE":
            return obj.author == request.user or obj.post.author == request.user
        
        # For other methods (PUT, PATCH), only allow the comment author
        return obj.author == request.user