from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator


class Post(models.Model):
    id = models.AutoField(primary_key=True, validators=[MaxValueValidator(999999)], editable=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Post by {self.author.email} on {self.created_at}"

    @property
    def likes_count(self):
        return self.likes.count()


class PostImage(models.Model):
    id = models.AutoField(primary_key=True, validators=[MaxValueValidator(999999)], editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to='posts/images/')

    def __str__(self):
        return f"Image for Post #{self.post.id}"


class PostLike(models.Model):
    
    id = models.AutoField(primary_key=True, validators=[MaxValueValidator(999999)], editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="liked_posts")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("post", "user")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} liked Post {self.post.id}"


class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment by {self.author.email} on Post {self.post.id}"
