from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from .forms import ChangeEmailForm, ChangePasswordForm, CourseForm, SemesterForm
from accounts.models import Course


class ManagerView(View):
    def get(self, request):
        return render(request, "manager_dashboard.html")


class ManagerAccountView(LoginRequiredMixin, View):
    def get(self, request):
        password_form = ChangePasswordForm()
        email_form = ChangeEmailForm()

        return render(request, "manager_account.html", {"email_form": email_form,
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

        return render(request, "manager_account.html", {"password_form": password_form,
                                                        'email_form': email_form})


class CourseCreateView(View):
    def get(self, request, *args, **kwargs):
        course_create_form = CourseForm()
        courses = Course.objects.all()

        paginator = Paginator(courses, 5)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'manager_courses.html', {'form': course_create_form, 'page_obj': page_obj})

    def post(self, request, *args, **kwargs):
        course_create_form = CourseForm(request.POST)
        if course_create_form.is_valid():
            course = course_create_form.save(commit=False)
            if course.can_be_created():
                course.save()
                messages.success(request, 'Course has been created successfully.')
                return redirect(reverse('CreateCoursePage'))
            else:
                messages.error(request, 'The semester has either not started or has already ended.')
        else:
            courses = Course.objects.all()
            paginator = Paginator(courses, 5)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            return render(request, 'manager_courses.html', {'form': course_create_form, 'page_obj': page_obj})


class SemesterCreateView(View):
    def get(self, request):
        form = SemesterForm()
        return render(request, 'manager_semester.html', {'form': form})

    def post(self, request):
        form = SemesterForm(request.POST)
        if form.is_valid():
            semester = form.save(commit=False)
            semester.save()
            messages.success(request, 'Semester has been created successfully.')
            return redirect(reverse('CreateSemesterPage'))

        return render(request, 'manager_semester.html', {'form': form})

