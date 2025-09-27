from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RequestOTPView, VerifyOTPView, SignupView, LoginView, ResetPasswordView, ProfileView, UserPublicProfileView, CompanyViewSet, MyCompanyView, ChangePasswordView, ResendOTPView
from .follow_views import FollowCreateView, UnfollowView
from .views import UserFollowersListView, UserFollowingUsersListView, UserFollowingCompaniesListView, UserListView


router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company')

urlpatterns = [
    path("auth/request-otp/", RequestOTPView.as_view(), name="request-otp"),
    path("auth/resend-otp/", ResendOTPView.as_view(), name="resend-otp"),
    path("auth/verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("auth/signup/", SignupView.as_view(), name="signup"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/<int:id>/", UserPublicProfileView.as_view(), name="user-profile-detail"),
    path("profile/<int:id>/followers/", UserFollowersListView.as_view(), name='user-followers'),
    path("profile/<int:id>/following/users/", UserFollowingUsersListView.as_view(), name='user-following-users'),
    path("profile/<int:id>/following/companies/", UserFollowingCompaniesListView.as_view(), name='user-following-companies'),
    path("my-company/", MyCompanyView.as_view(), name="my-company"),
    path("", include(router.urls)),
    path("follow/", FollowCreateView.as_view(), name="follow-create"),
    path("unfollow/user/<int:user_id>/", UnfollowView.as_view(), name="unfollow-user"),
    path("unfollow/company/<int:company_id>/", UnfollowView.as_view(), name="unfollow-company"),
    path("users/", UserListView.as_view(), name="user-list"),
]