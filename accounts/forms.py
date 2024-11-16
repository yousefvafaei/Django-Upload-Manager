from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from accounts.models import CustomUser


class CustomUserCreationForm(forms.ModelForm):
    """
    Form for creating a new CustomUser with email and password confirmation.

    This form allows the creation of a new user, requiring the user to enter
    and confirm their password. It performs validation to ensure the passwords
    match before saving the user.
    """
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('email', 'password1', 'password2')

    def clean_password2(self):
        """
        Validates that the two password entries match.
        """
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError('passwords dont match')
        return password2

    def save(self, commit: True):
        """
        Save the user with the hashed password.

        This method hashes the password and saves the user instance to the database.
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password2'])
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


class UserRegistrationForm(forms.Form):
    """
    Simple form for user registration with email and password.

    This form requires the user to input their email and password, and checks
    if the email is already registered in the system.
    """
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        """
        Validates that the email is not already in use.
        """
        email = self.cleaned_data['email']
        user = CustomUser.objects.filter(email=email).exists()
        if user:
            raise ValidationError('This email already exists!')
        return email


class UserLoginForm(forms.Form):
    """
    Form for user login with email and password.

    This form allows users to input their email and password for authentication.
    """
    email = forms.CharField(max_length=50)
    password = forms.CharField(widget=forms.PasswordInput)
