# job_portal/posts/admin.py
from django.contrib import admin
from .models import Post, PostImage, PostLike

class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 0
    readonly_fields = ('image',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'created_at')
    inlines = [PostImageInline]
    readonly_fields = ('created_at', 'updated_at')

@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'image')
    readonly_fields = ('id',)

@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'user', 'created_at')
    search_fields = ('user__email', 'post__id')
    readonly_fields = ('id', 'created_at')
