from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.core.validators import MaxValueValidator


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
    JOBSEEKER = "jobseeker"
    EMPLOYER = "employer"
    USER_TYPES = [
        (JOBSEEKER, "Jobseeker"),
        (EMPLOYER, "Employer"),
    ]

    id = models.AutoField(primary_key=True, validators=[MaxValueValidator(999999)], editable=False)
    email = models.EmailField(unique=True, db_index=True)

    first_name = models.CharField(max_length=120, blank=True)
    last_name = models.CharField(max_length=120, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)

    user_type = models.CharField(max_length=20, choices=USER_TYPES, default=JOBSEEKER)

    # ✅ Media Fields
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    cover_picture = models.ImageField(upload_to="covers/", blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

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


class CompanyProfile(models.Model):
    id = models.AutoField(primary_key=True, validators=[MaxValueValidator(999999)], editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="company_profile")
    company_name = models.CharField(max_length=255)
    company_description = models.TextField(blank=True)
    company_website = models.URLField(blank=True)
    company_size = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    company_logo = models.ImageField(upload_to="company_logos/", null=True, blank=True)
    headquarters_location = models.CharField(max_length=255, blank=True)
    is_approved = models.BooleanField(default=False)

    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['company_name']
        verbose_name = "Company Profile"
        verbose_name_plural = "Company Profiles"

    def __str__(self):
        return self.company_name

class Skill(models.Model):
    """
    A simple skill model. Skills are reusable and can be shared across users.
    """
    id = models.AutoField(primary_key=True, validators=[MaxValueValidator(999999)], editable=False)
    name = models.CharField(max_length=120, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Skill"
        verbose_name_plural = "Skills"

    def __str__(self):
        return self.name

class JobSeekerProfile(models.Model):
    id = models.AutoField(primary_key=True, validators=[MaxValueValidator(999999)], editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="jobseeker_profile")
    resume = models.FileField(upload_to="resumes/", null=True, blank=True)
    skills = models.ManyToManyField(Skill, blank=True, related_name="jobseekers")
    # education = models.TextField(blank=True)
    # experience = models.JSONField(default=list, blank=True)  # ✅ Structured experience data
    # expected_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"JobSeekerProfile({self.user.email})"

class Education(models.Model):
    """
    Multiple education records per JobSeekerProfile.
    Period is stored as a flexible string to allow different formats (2021 March - 2025 April, 2021-2025, etc.)
    """
    id = models.AutoField(primary_key=True, validators=[MaxValueValidator(999999)], editable=False)
    profile = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE, related_name="educations")
    degree = models.CharField(max_length=255)
    institution = models.CharField(max_length=255, blank=True)
    period = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Education"
        verbose_name_plural = "Educations"

    def __str__(self):
        return f"{self.degree} @ {self.institution}"

class Experience(models.Model):
    """
    Multiple experience records per JobSeekerProfile.
    Period is a flexible string (supports Present).
    """
    id = models.AutoField(primary_key=True, validators=[MaxValueValidator(999999)], editable=False)
    profile = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE, related_name="experiences")
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    period = models.CharField(max_length=255, blank=True)  # flexible representation
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Experience"
        verbose_name_plural = "Experiences"

    def __str__(self):
        return f"{self.title} @ {self.company}"
        
class EmployerProfile(models.Model):
    id = models.AutoField(primary_key=True, validators=[MaxValueValidator(999999)], editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employer_profile")
    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name="employers",
        null=True,
        blank=True
    )
    job_title = models.CharField(max_length=100, blank=True)
    is_company_admin = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} ({self.company.company_name if self.company else 'No Company'})"

    @property
    def has_company(self):
        return self.company is not None


class Follow(models.Model):
    id = models.AutoField(primary_key=True, validators=[MaxValueValidator(999999)], editable=False)
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following"
    )
    following_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="followers",
        null=True,
        blank=True
    )
    following_company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name="followers",
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "following_user"], name="unique_user_follow"),
            models.UniqueConstraint(fields=["follower", "following_company"], name="unique_company_follow"),
            models.CheckConstraint(
                check=(
                    (models.Q(following_user__isnull=False) & models.Q(following_company__isnull=True)) |
                    (models.Q(following_user__isnull=True) & models.Q(following_company__isnull=False))
                ),
                name="follow_xor_check"
            ),
        ]

    def __str__(self):
        if self.following_user:
            return f"{self.follower.email} follows {self.following_user.email}"
        else:
            return f"{self.follower.email} follows {self.following_company.company_name}"
