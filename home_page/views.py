from django.contrib import messages
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.views import View
from django.shortcuts import render, redirect
from .forms import LoginForm, RegistrationForm, ForgotPasswordForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from accounts.models import Profile


class Homeview(View):
    def get(self, request):
        form = LoginForm()
        return render(request, "home.html", {"form": form})

    def post(self, request):
        form = LoginForm(request.POST or None)

        if form.is_valid():
            id = form.cleaned_data.get('id')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=id, password=password)

            if user is not None:
                login(request, user)
                login_role = Profile.objects.get(user_id=id).user_type

                if login_role == 'student':
                    return redirect('student/')
                elif login_role == 'instructor':
                    return redirect('instructor/')
                else:
                    return redirect('manager/')

            else:
                messages.success(request, 'There is no user or password is wrong')
                print("There is no user")

        return render(request, "home.html", {"form": form})


class RegistrationView(View):

    def get(self, request):
        form = RegistrationForm()
        return render(request, "registration.html", {"form": form})

    def post(self, request):
        form = RegistrationForm(request.POST or None)

        if form.is_valid():
            id = form.cleaned_data.get('id')
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            email = form.cleaned_data.get('email')
            password = get_random_string(length=16)

            if User.objects.filter(id=id).exists():
                messages.success(request, "There is already user!")
            elif User.objects.filter(email=email).exists():
                messages.success(request, "The email has already been taken!")
            else:
                user = User.objects.create_user(id=id,
                                                username=id,
                                                password=password,
                                                email=email,
                                                first_name=first_name,
                                                last_name=last_name,
                                                is_active=False)

                Profile.objects.create(user=user, user_type='student')

                send_mail('Welcome to CIES',
                          f'Hello {user.first_name} {user.last_name},\n\nYour new password is: {password}',
                          'mehmetalpkaynar@gmail.com',
                          [email],
                          fail_silently=False)
                messages.success(request, "The student has been successfully created, please wait for the enrollment")

        return render(request, 'registration.html', {"form": form})


class ForgotPasswordView(View):

    def get(self, request):
        form = ForgotPasswordForm()
        return render(request, "ForgotPassword.html", {"form": form})

    def post(self, request):
        form = ForgotPasswordForm(request.POST or None)

        if form.is_valid():
            id = form.cleaned_data.get('id')
            print('If there is an e-mail matching with provided Student-ID, we sent an e-mail about resetting '
                  'your password.')

            if User.objects.filter(id=id):
                user = User.objects.get(id=id)
                new_password = get_random_string(length=16)
                user.set_password(new_password)
                user.save()
                messages.success(request, 'If there is an e-mail matching with provided Student-ID, we sent an e-mail '
                                          'about resetting '
                                          'your password.')
                send_mail('Forgot Password',
                          f'Hello {user.first_name} {user.last_name},\n\nYour new password is: {new_password}\nPlease '
                          f'change your password immediately',
                          'mehmetalpkaynar@gmail.com',
                          [user.email],
                          fail_silently=False)
            else:
                messages.success(request, 'If there is an e-mail matching with provided Student-ID, we sent an e-mail '
                                          'about resetting '
                                          'your password.')

        return render(request, "ForgotPassword.html", {"form": form})
