from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from .managers import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that extends AbstractBaseUser and PermissionsMixin
    to provide custom user authentication and authorization features.

    Attributes:
        email (str): The email address of the user. It is used as the username.
        is_active (bool): A flag indicating whether the user account is active. Default is True.
        is_admin (bool): A flag indicating whether the user has admin rights. Default is False.
        is_superuser (bool): A flag indicating whether the user has superuser rights. Default is False.
    """
    email = models.EmailField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    @property
    def is_staff(self):
        return self.is_admin


class Profile(models.Model):
    """
    Profile model that stores additional user information such as first name,
    last name, and profile image (cover photo).

    Attributes:
        user (CustomUser): A one-to-one relationship with the CustomUser model.
        first_name (str): The user's first name.
        last_name (str): The user's last name.
        cover (ImageField): The user's profile cover image, optional.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=250)
    last_name = models.CharField(max_length=250)
    cover = models.ImageField(upload_to="accounts/profiles", null=True, blank=True)

    def __str__(self):
        return self.user.email