import os
import time
from django.dispatch import receiver
from django.db.models.signals import post_delete
from .models import File


@receiver(post_delete, sender=File)
def delete_file_on_model_delete(sender, instance, **kwargs):
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
