import os
import time
from django.dispatch import receiver
from django.db.models.signals import post_delete
from .models import File


@receiver(post_delete, sender=File)
def delete_file_on_model_delete(sender, instance, **kwargs):
    """
    Signal handler to delete the file and its thumbnail from the filesystem
    when a File model instance is deleted.

    Args:
        sender (Model): The model class that sent the signal (File).
        instance (File): The instance of the File model being deleted.
        **kwargs: Additional keyword arguments.

    This function attempts to delete the file and its associated thumbnail.
    It will retry up to 5 times if the file is being used (i.e., a `PermissionError` occurs).
    """
    if instance.file:
        file_path = instance.file.path
        attempts = 5
        for _ in range(attempts):
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                break
            except PermissionError as e:
                time.sleep(0.1)  # Wait and retry if file is being used
            else:
                raise e

    if instance.thumbnail:
        thumbnail_path = instance.thumbnail.path
        attempts = 5
        for _ in range(attempts):
            try:
                if os.path.isfile(thumbnail_path):
                    os.remove(thumbnail_path)
                break
            except PermissionError as e:
                time.sleep(0.1)  # Wait and retry if file is being used
            else:
                raise e
