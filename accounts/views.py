from django.shortcuts import redirect, render
from django.contrib import messages
from django.views import View
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import CustomUser
from .forms import CustomUserCreationForm, UserLoginForm


class UserRegisterView(View):
    """
    View for user registration using CustomUserCreationForm.
    Handles form validation, user creation, and error/success messages.
    """
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'

    def get(self, request):
        form = self.form_class()
        return self.render_form(form)

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Auto-login after successful registration
            messages.success(request, 'You have registered successfully!', extra_tags='success')
            return redirect('uploadmanager:home')
        else:
            messages.error(request, 'Registration failed. Please fix the errors below.', extra_tags='danger')
        return self.render_form(form)

    def render_form(self, form):
        return render(self.request, self.template_name, {'form': form})


class UserLogoutView(LoginRequiredMixin, View):
    """
    View to handle user logout.

    This view logs the user out and redirects them to the login page.

    Methods:
        get(request): Logs the user out and redirects to the login page.
    """
    def get(self, request):
        logout(request)
        messages.success(request, 'You have logged out successfully.', extra_tags='success')
        return redirect('accounts:user_login')


class UserLoginView(View):
    """
    View for user login using UserLoginForm.
    Handles form validation, user authentication, and success/error messages.
    """
    form_class = UserLoginForm
    template_name = 'accounts/login.html'

    def get(self, request):
        form = self.form_class()
        return self.render_form(form)

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            if user:
                login(request, user)
                messages.success(request, 'Logged in successfully!', extra_tags='info')
                return redirect('uploadmanager:home')
            messages.error(request, 'Invalid email or password!', extra_tags='warning')
        else:
            messages.error(request, 'Please correct the errors below.', extra_tags='danger')
        return self.render_form(form)

    def render_form(self, form):
        return render(self.request, self.template_name, {'form': form})
