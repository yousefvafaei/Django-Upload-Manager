from django.contrib import admin
from .models import File, Folder


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    """
    Admin interface customization for the File model.

    This class customizes the File model's representation in the Django admin
    """
    list_display = ('name', 'type', 'get_size_in_mb', 'user', 'created_at', 'updated_at', 'get_folder')
    list_filter = ('type', 'user', 'created_at')  # Adding filters for file type, user, and creation date
    search_fields = ('name', 'user__username')  # Adding search by file name and user name
    ordering = ('-created_at',)  # Ordering by newest first

    def get_size_in_mb(self, obj):
        """
        Returns the size of the file in megabytes with two decimal points.
        """
        return f"{obj.size / (1024 * 1024):.2f} MB"

    get_size_in_mb.short_description = 'Size'

    def get_folder(self, obj):
        """
        Returns the name of the folder the file is in, or 'No Folder' if not assigned.
        """
        return obj.folder.name if obj.folder else 'No Folder'

    get_folder.short_description = 'Folder'


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    """
    Admin interface customization for the Folder model.

    This class customizes the Folder model's representation in the Django admin
    """
    list_display = ('name', 'user', 'is_parent', 'created_at', 'updated_at')
    list_filter = ('user', 'created_at')  # Adding filters for user and creation date
    search_fields = ('name', 'user__username')  # Adding search by folder name and user name
    ordering = ('-created_at',)  # Ordering by newest first
