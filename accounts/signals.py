from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save

from .models import CustomUser, Profile


@receiver(post_save, sender=CustomUser)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
