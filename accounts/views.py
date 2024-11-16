from django.shortcuts import redirect, render
from django.contrib import messages
from django.views import View
from .forms import UserRegistrationForm, UserLoginForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import CustomUser


class UserRegisterView(View):
    """
    View for user registration.

    Handles the rendering of the registration form and processing the form submission.
    If the form is valid, a new user is created and a success message is shown.

    Attributes:
        form_class (Form): The form class used for user registration.
        template_name (str): The template used to render the registration page.

    Methods:
        get(request): Renders the registration page with an empty form.
        post(request): Processes the form submission to register a new user.
    """
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            CustomUser.objects.create_user(email=cd['email'], password=cd['password'])
            messages.success(request, 'You have registered successfully!', extra_tags='success')
            return redirect('uploadmanager:home')
        else:
            messages.error(request, 'There was an error with your registration.', extra_tags='danger')
        return render(request, self.template_name, {'form': form})


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
    View for user login.

    Handles the rendering of the login form and processing the form submission.
    If the form is valid, the user is authenticated and logged in.

    Attributes:
        form_class (Form): The form class used for user login.
        template_name (str): The template used to render the login page.

    Methods:
        get(request): Renders the login page with an empty form.
        post(request): Processes the form submission to log the user in.
    """
    form_class = UserLoginForm
    template_name = 'accounts/login.html'

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request, email=cd['email'], password=cd['password'])
            if user is not None:
                login(request, user)
                messages.success(request, 'You have logged in successfully!', extra_tags='info')
                return redirect('uploadmanager:home')
            else:
                messages.error(request, 'Invalid email or password!', extra_tags='warning')
        else:
            messages.error(request, 'Please correct the errors below.', extra_tags='danger')

        return render(request, self.template_name, {'form': form})
