import uuid
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager
)

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if not password:
            raise ValueError("Password is required")
        user.set_password(password)
        user.is_active = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    CANDIDATE = "candidate"
    EMPLOYER = "employer"
    USER_TYPES = [
        (CANDIDATE, "Candidate"),
        (EMPLOYER, "Employer"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)

    first_name = models.CharField(max_length=120, blank=True)
    last_name = models.CharField(max_length=120, blank=True)

    phone_number = models.CharField(max_length=20, blank=True)

    user_type = models.CharField(max_length=20, choices=USER_TYPES, default=CANDIDATE)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)

    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.email


class JobSeekerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="jobseeker_profile")
    resume = models.FileField(upload_to="resumes/", null=True, blank=True)
    skills = models.TextField(blank=True)  # comma-separated list
    education = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    expected_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preferred_location = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"JobSeekerProfile({self.user.email})"


class EmployerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employer_profile")
    company_name = models.CharField(max_length=255, blank=True)
    company_description = models.TextField(blank=True)
    company_website = models.URLField(blank=True)
    company_size = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    company_logo = models.ImageField(upload_to="company_logos/", null=True, blank=True)

    def __str__(self):
        return f"EmployerProfile({self.user.email})"
