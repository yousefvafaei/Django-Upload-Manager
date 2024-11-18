from django.contrib.auth.models import BaseUserManager


class CustomUserManager(BaseUserManager):
    """
    Custom manager for CustomUser model to handle user creation and management.

    This manager provides methods for creating regular users and superusers.

    Methods:
        create_user(email, password):
            Creates and returns a regular user with an email and password.

        create_superuser(email, password):
            Creates and returns a superuser with email, password, and admin permissions.
    """
    def create_user(self, email, password):

        if not email:
            raise ValueError('user must have email')

        user = self.model(email=self.normalize_email(email),)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(email, password)
        user.is_admin = True
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user