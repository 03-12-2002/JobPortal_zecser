from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, JobSeekerProfile, EmployerProfile, CompanyProfile, Follow

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "phone_number", "user_type", "is_staff", "is_superuser")
    search_fields = ("email", "first_name", "last_name", "phone_number")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone_number", "user_type", "profile_picture")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2"),
        }),
    )

    add_form_template = None
    readonly_fields = ("date_joined",)
    list_filter = ("is_staff", "is_superuser", "is_active", "groups", "user_type")

@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'industry', 'headquarters_location', 'is_approved', 'date_created')
    list_filter = ('is_approved', 'industry', 'date_created')
    search_fields = ('company_name', 'industry', 'headquarters_location')
    readonly_fields = ('date_created', 'id')
    fieldsets = (
        (None, {
            'fields': ('id', 'company_name', 'is_approved')
        }),
        ('Details', {
            'fields': ('industry', 'company_size', 'headquarters_location')
        }),
        ('Media & Links', {
            'fields': ('company_description', 'company_website', 'company_logo')
        }),
    )

@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'company_name', 'job_title', 'is_company_admin')
    list_filter = ('is_company_admin', 'company__is_approved', 'company')
    search_fields = ('user__email', 'company__company_name', 'job_title')
    autocomplete_fields = ('user', 'company')
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'

    def company_name(self, obj):
        return obj.company.company_name if obj.company else "No Company Linked"
    company_name.short_description = 'Company'
    company_name.admin_order_field = 'company__company_name'

@admin.register(JobSeekerProfile)
class JobSeekerProfileAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'location')
    search_fields = ('user__email', 'skills', 'location')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Job Seeker'

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower_email', 'following_object', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('follower__email', 'following_user__email', 'following_company__company_name')

    def follower_email(self, obj):
        return obj.follower.email
    follower_email.short_description = 'Follower'

    def following_object(self, obj):
        if obj.following_user:
            return f"User: {obj.following_user.email}"
        elif obj.following_company:
            return f"Company: {obj.following_company.company_name}"
        return "Unknown"
    following_object.short_description = 'Following'