from django.urls import path
from .views import RequestOTPView, VerifyOTPView, SignupView, LoginView, ResetPasswordView

urlpatterns = [
    path("auth/request-otp/", RequestOTPView.as_view(), name="request-otp"),
    path("auth/verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("auth/signup/", SignupView.as_view(), name="signup"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/reset-password/", ResetPasswordView.as_view(), name="reset-password"),
]
