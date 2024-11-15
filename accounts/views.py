from django.shortcuts import redirect, render
from django.contrib import messages
from django.views import View
from .forms import UserRegistrationForm, UserLoginForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import CustomUser


class UserRegisterView(View):
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
    def get(self, request):
        logout(request)
        messages.success(request, 'You have logged out successfully.', extra_tags='success')
        return redirect('accounts:user_login')


class UserLoginView(View):
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
