from django.core.cache import cache
from django.conf import settings
from django.core.mail import send_mail
from datetime import timedelta
from .utils import generate_otp

OTP_EXPIRE_SECONDS = 300  # 5 minutes

def send_otp_email(email: str, purpose: str):
    """
    Generate and send OTP to email.
    Purpose: 'register' or 'reset'
    """
    otp = generate_otp()
    cache_key = f"otp:{purpose}:{email}"
    cache.set(cache_key, otp, OTP_EXPIRE_SECONDS)

    subject = f"Your {purpose.capitalize()} OTP Code"
    message = f"Your OTP code is: {otp}. It is valid for 5 minutes."
    from_email = settings.DEFAULT_FROM_EMAIL

    send_mail(subject, message, from_email, [email])

    return otp  # for debugging/testing


def verify_otp(email: str, otp: str, purpose: str) -> bool:
    """Check OTP validity."""
    cache_key = f"otp:{purpose}:{email}"
    cached_otp = cache.get(cache_key)
    if cached_otp and cached_otp == otp:
        cache.delete(cache_key)  # prevent reuse
        return True
    return False
