from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.forms import formset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.views import View
from .forms import ChangeEmailForm, ChangePasswordForm, CourseForm, SemesterForm, CreateUserForm, SectionForm
from accounts.models import Course, Profile, Section


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


class AddUserView(View):
    def get(self, request):
        add_user_form = CreateUserForm()
        return render(request, 'manager_users.html', {'form': add_user_form})

    def post(self, request):
        add_user_form = CreateUserForm(request.POST)
        if add_user_form.is_valid():
            id = add_user_form.cleaned_data.get('id')
            first_name = add_user_form.cleaned_data.get('first_name')
            last_name = add_user_form.cleaned_data.get('last_name')
            email = add_user_form.cleaned_data.get('email')
            user_type = add_user_form.cleaned_data.get('user_type')
            password = get_random_string(length=16)

            if User.objects.filter(id=id).exists():
                messages.success(request, "There is already user in db")
            else:
                user = User.objects.create_user(id=id,
                                                username=id,
                                                password=password,
                                                email=email,
                                                first_name=first_name,
                                                last_name=last_name)

                Profile.objects.create(user=user, user_type=user_type)
                send_mail('Welcome to CIES',
                          f'Hello {user.first_name} {user.last_name},\n\nYour new password is: {password}',
                          'mehmetalpkaynar@gmail.com',
                          [email],
                          fail_silently=False)
                messages.success(request, "The user has been successfully created, please wait for the enrollment")

            return redirect(reverse("AddUserPage"))

        return render(request, 'manager_users.html', {'form': add_user_form})


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


class CourseEditView(View):
    template_name = 'manager_edit_course.html'
    SectionFormSet = formset_factory(SectionForm, extra=0)
    section_formset_class = SectionFormSet

    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        sections = course.sections.all()
        initial_data = [{'classroom': section.Classroom or None} for section in sections]
        print(initial_data)
        section_formset = self.section_formset_class(initial=initial_data)
        context = {
            'sections': sections,
            'section_formset': section_formset,
        }
        return render(request, self.template_name, context)

    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        sections = course.sections.all()
        section_formset = self.section_formset_class(request.POST)
        if section_formset.is_valid():
            for i, form in enumerate(section_formset):
                section = sections[i]  # Convert the index to an integer
                classroom = form.cleaned_data.get('Classroom')  # Update the field name
                instructors = form.cleaned_data.get('Instructors')  # Update the field name
                section.Classroom = classroom
                section.Instructors.set(instructors)
                section.save()
            return redirect(reverse('CreateCoursePage'))
        else:
            print("yo")
            print(section_formset.errors)
            print(section_formset.non_form_errors())

        context = {
            'sections': sections,
            'section_formset': section_formset,
        }
        return render(request, self.template_name, context)
