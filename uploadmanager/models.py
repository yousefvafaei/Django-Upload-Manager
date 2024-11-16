import os
import random
import string
import uuid

from django.utils.text import slugify
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image
from moviepy.editor import VideoFileClip
import mimetypes
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

DEFAULT_THUMBNAIL_PATH = "default_thumbnail.jpg"
THUMBNAIL_SIZE = (100, 100)
THUMBNAIL_FOLDER = "media/thumbnails"


# Custom validator for folder name field
def validate_name(value):
    invalid_chars = r"[@#%$*&<>?|/:]"
    if any(char in value for char in invalid_chars):
        raise ValidationError(
            "Folder name cannot contain invalid characters: @#%$*&<>?|/:"
        )


class Folder(models.Model):
    name = models.CharField(max_length=255, validators=[validate_name])
    slug = models.SlugField(max_length=255, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='folders', on_delete=models.CASCADE)
    is_parent = models.ForeignKey('self', related_name='subfolders', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Create slug from name if not set
        if not self.slug:
            self.slug = slugify(self.name)

        # Preventing creation of duplicate folders in the same parent
        count = 0
        while Folder.objects.filter(
                name=self.name, is_parent=self.is_parent, user=self.user
        ).exists():
            count += 1
            if self.name[-1].isdigit():
                self.name = self.name[:-1]
            self.name += str(count)

        # Ensure slug uniqueness by appending UUID if needed
        if Folder.objects.filter(slug=self.slug).exists():
            self.slug = f"{self.slug}-{uuid.uuid4().hex[:8]}"  # Append UUID to slug to make it unique

        super().save(*args, **kwargs)

    def get_nested_path(self):
        """Return the full nested path with slugs for URL."""
        path = [{"name": self.name, "slug": self.slug}]  # Start with current folder name and slug
        parent = self.is_parent

        while parent:
            path.insert(0, {"name": parent.name, "slug": parent.slug})  # Insert parent folder name and slug
            parent = parent.is_parent  # Move to the next parent folder

        return path  # Return list of folder names and slugs

    class Meta:
        unique_together = ("name", "is_parent", "user")


def validate_file_type(value):
    valid_mime_types = {
        "image/jpeg", "image/jpg", "image/png", "image/gif", "image/bmp", "image/tiff",
        "video/mp4", "video/mkv", "video/wmv", "video/mov", "video/avi", "video/mpeg",
        "video/quicktime", "video/x-msvideo", "video/x-ms-wmv"
    }

    mime_type, _ = mimetypes.guess_type(value.name)

    if mime_type not in valid_mime_types:
        raise ValidationError("Unsupported file type. Only videos and images are supported.")


def validate_file_size(value):
    mime_type, _ = mimetypes.guess_type(value.name)

    if mime_type and mime_type.startswith("image"):
        max_size_mb = 7  # Maximum size for images is 7 MB
    else:
        max_size_mb = 50  # Maximum size for other files is 50 MB

    max_size_bytes = max_size_mb * 1024 * 1024
    if value.size > max_size_bytes:
        raise ValidationError(f"File size exceeds the maximum limit of {max_size_mb} MB.")


class File(models.Model):
    FILE_TYPE_CHOICE = (
        ('img', 'Image'),
        ('vid', 'Video')
    )

    name = models.CharField(max_length=255, blank=True, null=True)
    file = models.FileField(upload_to='files/', validators=[validate_file_type, validate_file_size])
    size = models.IntegerField(blank=True, null=True)
    type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICE)
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='files', on_delete=models.CASCADE)
    folder = models.ForeignKey('Folder', on_delete=models.CASCADE, related_name='files', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name or os.path.basename(self.file.name)
        self.size = self.size or self.file.size
        self.type = self.type or self._choose_file_type()

        super().save(*args, **kwargs)

        if not self.thumbnail:
            self._create_thumbnail()

    def _choose_file_type(self):
        mime_type, _ = mimetypes.guess_type(self.file.name)
        if mime_type:
            return "image" if mime_type.startswith("image") else "video"
        raise ValidationError("Invalid file")

    def get_file_size_in_mb(self):
        """Convert file size from bytes to MB with 2 decimal precision."""
        size_in_mb = self.file.size / (1024 * 1024)  # Convert to MB
        return round(size_in_mb, 2)  # Round to 2 decimal places

    def _create_thumbnail(self):
        os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)
        mime_type, _ = mimetypes.guess_type(self.file.name)

        if mime_type and mime_type.startswith("image"):
            self._create_image_thumbnail()
        elif mime_type and mime_type.startswith("video"):
            self._create_video_thumbnail()

    def _create_image_thumbnail(self):
        try:
            image = Image.open(self.file)
            image.thumbnail(THUMBNAIL_SIZE, Image.LANCZOS)

            thumbnail_filename = os.path.join(THUMBNAIL_FOLDER, os.path.basename(self.file.name))
            image.save(thumbnail_filename)

            self.thumbnail = thumbnail_filename.replace("media/", "")
            self.save()
        except Exception as error:
            logger.error(f"Failed to create image thumbnail for {self.file.name}: {error}")
            self.thumbnail = DEFAULT_THUMBNAIL_PATH
            self.save()

    def _create_video_thumbnail(self):
        try:
            file_path = self.file.path
            thumbnail_filename = os.path.join(THUMBNAIL_FOLDER, os.path.basename(self.file.name) + ".jpg")

            with VideoFileClip(file_path) as clip:
                frame = clip.get_frame(1)  # Capture frame at 1 second
                thumbnail = Image.fromarray(frame)
                thumbnail.thumbnail(THUMBNAIL_SIZE)
                thumbnail.save(thumbnail_filename)

            self.thumbnail = thumbnail_filename.replace("media/", "")
            self.save()
        except Exception as error:
            logger.error(f"Failed to create video thumbnail for {self.file.name}: {error}")
            self.thumbnail = DEFAULT_THUMBNAIL_PATH
            self.save()

    class Meta:
        unique_together = ("name", "folder", "user")
