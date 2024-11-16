from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save

from .models import CustomUser, Profile


@receiver(post_save, sender=CustomUser)
def create_profile(sender, instance, created, **kwargs):
    """
    Signal receiver to create a Profile instance when a new CustomUser is created.

    This function is automatically called when a new CustomUser instance is saved.
    It creates a corresponding Profile instance for the newly created user.
    """
    if created:
        Profile.objects.create(user=instance)
