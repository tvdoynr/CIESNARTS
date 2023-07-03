from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View
from .forms import ChangeEmailForm, ChangePasswordForm


class InstructorView(View):
    def get(self, request):
        return render(request, "instructor_dashboard.html")


class InstructorAccountView(LoginRequiredMixin, View):
    def get(self, request):
        password_form = ChangePasswordForm()
        email_form = ChangeEmailForm()

        return render(request, "instructor_account.html", {"email_form": email_form,
                                                           "password_form": password_form})

    def post(self, request):
        if "password" in request.POST:
            password_form = ChangePasswordForm(request.POST)
            email_form = ChangeEmailForm()
            if password_form.is_valid():
                current_password = password_form.cleaned_data.get("current_password")
                new_password = password_form.cleaned_data.get("new_password")
                new_password_again = password_form.cleaned_data.get("new_password_again")

                user = authenticate(request, username=request.user.username, password=current_password)

                if user is not None:
                    request.user.set_password(new_password)
                    request.user.save()
                    login(request, request.user)
                    messages.success(request, 'The password has been changed successfully')
                else:
                    messages.error(request, 'The current password is wrong!')

        elif "email" in request.POST:
            email_form = ChangeEmailForm(request.POST)
            password_form = ChangePasswordForm()
            if email_form.is_valid():
                new_email_address = email_form.cleaned_data.get('new_email_address')
                confirm_password = email_form.cleaned_data.get('confirm_password')

                user = authenticate(request, username=request.user.id, password=confirm_password)

                if user is not None:
                    request.user.email = new_email_address
                    request.user.save()
                    messages.success(request, 'The email has been changed successfully')
                else:
                    messages.success(request, 'The password is wrong!')

        else:
            password_form = ChangePasswordForm()
            email_form = ChangeEmailForm()

        return render(request, "instructor_account.html", {"password_form": password_form, 'email_form': email_form})
