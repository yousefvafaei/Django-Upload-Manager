import re
from django import forms
from .models import File, Folder, validate_file_size


class FileUploadForm(forms.ModelForm):
    """
    Form for uploading a new file. Includes user-specific folder choices.
    """
    class Meta:
        model = File
        fields = ['file', 'folder']
        error_messages = {
            'file': {
                'required': 'Please select a file to upload.',
                'invalid': 'Invalid file format.',
            },
            'folder': {
                'required': 'Please select a folder.',
            },
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)


class FileUpdateForm(forms.ModelForm):
    """
    Form for updating an existing file's name.
    """
    class Meta:
        model = File
        fields = ['name']


class FolderCreateForm(forms.ModelForm):
    """
    Form for creating a new folder. Includes selection of parent folder if applicable.
    """
    class Meta:
        model = Folder
        fields = ['name', 'is_parent']


class FolderUpdateForm(forms.ModelForm):
    """
    Form for updating an existing folder's name.
    """
    class Meta:
        model = Folder
        fields = ['name']
