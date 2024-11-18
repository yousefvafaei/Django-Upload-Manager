from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.password_validation import validate_password

from accounts.models import CustomUser


class CustomUserCreationForm(forms.ModelForm):
    """
    Form for creating a new CustomUser with email and password confirmation,
    using Django's password validation system.
    """
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput,
        help_text="Your password must meet the system's complexity requirements."
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput,
        help_text="Enter the same password as before, for verification."
    )

    class Meta:
        model = CustomUser
        fields = ('email',)

    def clean_password1(self):
        """
        Validate the first password using Django's password validators.
        """
        password1 = self.cleaned_data.get('password1')
        validate_password(password1)  # Validate against AUTH_PASSWORD_VALIDATORS
        return password1

    def clean_password2(self):
        """
        Ensure the two password fields match.
        """
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError('Passwords do not match.')
        return password2

    def save(self, commit=True):
        """
        Save the user with the hashed password.
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])  # Use the first password
        if commit:
            user.save()
        return user


class CustomUserChangeForm(forms.ModelForm):
    """
    Form for updating a CustomUser's details, including password.

    This form displays the user's email, password (read-only), and the last login timestamp.
    Users can update their email and view their password but cannot directly modify the password here.
    """
    password = ReadOnlyPasswordHashField(
        help_text='you can change password using <a href=\"../password/\"> this form. </a>')

    class Meta:
        model = CustomUser
        fields = ('email', 'password', 'last_login')


class UserLoginForm(forms.Form):
    """
    Form for user login with email and password.

    This form allows users to input their email and password for authentication.
    """
    email = forms.CharField(max_length=50)
    password = forms.CharField(widget=forms.PasswordInput)
