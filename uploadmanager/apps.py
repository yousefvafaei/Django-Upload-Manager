from django.apps import AppConfig


class UploadmanagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'uploadmanager'

    def ready(self):
        from . import signals