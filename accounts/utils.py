import random

def generate_otp(length=6) -> str:
    """Generate a numeric OTP code of given length."""
    return "".join([str(random.randint(0, 9)) for _ in range(length)])
