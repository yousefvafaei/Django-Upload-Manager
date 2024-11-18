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
import magic

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

DEFAULT_THUMBNAIL_PATH = "default-thumbnail.jpg"
THUMBNAIL_SIZE = (100, 100)
THUMBNAIL_FOLDER = "media/thumbnails"


# Custom validator for folder name field
def validate_name(value):
    """
    Validates that the folder name does not contain invalid characters.

    Args:
        value (str): The folder name to be validated.

    Raises:
        ValidationError: If the folder name contains invalid characters.
    """
    invalid_chars = r"[@#%$*&<>?|/:]"
    if any(char in value for char in invalid_chars):
        raise ValidationError(
            "Folder name cannot contain invalid characters: @#%$*&<>?|/:"
        )


class Folder(models.Model):
    """
    A folder model for organizing files.

    Folders can have subfolders (is_parent) and are associated with a specific user.
    Each folder is uniquely identified by a combination of name and parent folder (if any).
    """
    name = models.CharField(max_length=255, validators=[validate_name])
    slug = models.SlugField(max_length=255, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='folders', on_delete=models.CASCADE)
    is_parent = models.ForeignKey('self', related_name='subfolders', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Override save method to generate unique slugs and ensure no duplicate folder names
        for the same user and parent folder.

        Args:
            *args: Additional arguments passed to save.
            **kwargs: Additional keyword arguments passed to save.
        """
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
        """
        Returns the full nested path of the folder, including all parent folders.

        Returns:
            list: A list of dictionaries containing folder names and slugs.
        """
        path = [{"name": self.name, "slug": self.slug}]
        parent = self.is_parent

        while parent:
            path.insert(0, {"name": parent.name, "slug": parent.slug})
            parent = parent.is_parent

        return path

    class Meta:
        unique_together = ("name", "is_parent", "user")


def validate_file_type(value):
    """
    Validates the MIME type of a file to ensure it is an accepted image or video format.
    """
    valid_mime_types = {
        "image/jpeg", "image/png", "image/gif", "image/bmp", "image/tiff",
        "video/mp4", "video/mkv", "video/wmv", "video/mov", "video/avi",
        "video/mpeg", "video/quicktime"
    }

    mime_detector = magic.Magic(mime=True)
    mime_type = mime_detector.from_buffer(value.read())
    value.seek(0)

    if mime_type not in valid_mime_types:
        raise ValidationError(f"Unsupported file type. Detected type: {mime_type}. Only videos and images are supported.")


def validate_file_size(value):
    """
    Validates the file size for both images and other file types.

    Args:
        value (File): The file to be validated.

    Raises:
        ValidationError: If the file size exceeds the allowed limit.
    """
    mime_type, _ = mimetypes.guess_type(value.name)

    if mime_type and mime_type.startswith("image"):
        max_size_mb = 7  # Maximum size for images is 7 MB
    else:
        max_size_mb = 50  # Maximum size for other files is 50 MB

    max_size_bytes = max_size_mb * 1024 * 1024
    if value.size > max_size_bytes:
        raise ValidationError(f"File size exceeds the maximum limit of {max_size_mb} MB.")


class File(models.Model):
    """
    A file model for storing user files such as images and videos.

    Each file is associated with a specific folder and user, and includes information such as file size,
    type, and a thumbnail if applicable.
    """
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
        """
        Override save method to assign file name, size, and type.
        Also, it generates a thumbnail for images and videos if not already present.

        Args:
            *args: Additional arguments passed to save.
            **kwargs: Additional keyword arguments passed to save.
        """
        self.name = self.name or os.path.basename(self.file.name)
        self.size = self.size or self.file.size
        self.type = self.type or self._choose_file_type()

        super().save(*args, **kwargs)

        if not self.thumbnail:
            self._create_thumbnail()

    def _choose_file_type(self):
        """
        Determines the file type (image or video) based on the file's MIME type.
        """
        mime_detector = magic.Magic(mime=True)
        mime_type = mime_detector.from_buffer(self.file.read())
        self.file.seek(0)  # Reset file pointer after reading

        if mime_type.startswith("image"):
            return "image"
        elif mime_type.startswith("video"):
            return "video"
        else:
            raise ValidationError(f"Invalid file type: {mime_type}")

    def get_file_size(self):
        """
        Returns the size of the file in a human-readable format.
        """
        size = self.size or self.file.size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    def _create_thumbnail(self):
        """
        Creates a thumbnail for the file, either from an image or video.

        This method creates a thumbnail image for image files and video files.
        """
        os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)
        mime_type, _ = mimetypes.guess_type(self.file.name)

        if mime_type and mime_type.startswith("image"):
            self._create_image_thumbnail()
        elif mime_type and mime_type.startswith("video"):
            self._create_video_thumbnail()

    def _create_image_thumbnail(self):
        """
        Creates a thumbnail for image files.

        This method generates a 100x100 thumbnail for an image file and saves it.
        If the thumbnail creation fails, a default thumbnail is used.
        """
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
        """
        Creates a thumbnail for video files.

        This method generates a 100x100 thumbnail by extracting a frame from the video
        at the 1-second mark and saves it as an image.
        """
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
