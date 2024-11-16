from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from .models import CustomUser, Profile
from .forms import CustomUserChangeForm, CustomUserCreationForm


class CustomUserAdmin(BaseUserAdmin):
    """
    Custom admin interface for managing CustomUser model in Django admin.

    This admin class allows the management of the CustomUser model with additional
    fields for user permissions and management options.
    """
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = ['email', 'is_admin']
    list_filter = ['is_admin']
    readonly_fields = ['last_login']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions',
         {'fields': ('is_active', 'is_admin', 'is_superuser', 'last_login', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {'fields': ('email', 'password1', 'password2')}),
    )

    search_fields = ['email']
    ordering = ['email']
    filter_horizontal = ('groups', 'user_permissions')

    def get_form(self, request, obj=None, **kwargs):
        """
        Override the get_form method to disable the 'is_superuser' field for non-superusers.

        Args:
            request (HttpRequest): The request object.
            obj (CustomUser, optional): The user object being edited, if any.
            **kwargs: Additional keyword arguments.

        Returns:
            form: The form instance with the 'is_superuser' field disabled for non-superusers.
        """
        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser
        if not is_superuser:
            form.base_fields['is_superuser'].disabled = True
        return form


admin.site.register(CustomUser, CustomUserAdmin)

admin.site.register(Profile)