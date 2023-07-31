import holidays
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.forms import formset_factory
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.views import View
from .forms import ChangeEmailForm, ChangePasswordForm, CourseForm, SemesterForm, CreateUserForm, SectionForm
from accounts.models import Course, Profile, Semester, Section


def user_is_manager(function):
    def wrap(request, *args, **kwargs):
        profile = Profile.objects.get(user=request.user)
        if profile.user_type == 'manager':
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


@method_decorator(login_required, name="dispatch")
@method_decorator(user_is_manager, name="dispatch")
class ManagerView(View):
    def get(self, request):
        return render(request, "manager_dashboard.html")


@method_decorator(login_required, name="dispatch")
@method_decorator(user_is_manager, name="dispatch")
class ManagerAccountView(View):
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


@method_decorator(login_required, name="dispatch")
@method_decorator(user_is_manager, name="dispatch")
class CourseCreateView(View):
    def get(self, request, *args, **kwargs):
        course_create_form = CourseForm()

        current_date = timezone.now().date()
        semester = Semester.objects.filter(start_date__lte=current_date, finish_date__gte=current_date).first()

        courses = Course.objects.filter(semester=semester).order_by("course_id")

        paginator = Paginator(courses, 5)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'manager_courses.html', {'form': course_create_form, 'page_obj': page_obj})

    def post(self, request, *args, **kwargs):
        if "delete_course" in request.POST:
            try:
                course_id = request.POST.get('course_id')
                print(course_id)
                course = Course.objects.get(pk=course_id)
                course.delete()
                return JsonResponse({"success": True})
            except:
                return JsonResponse({"success": False})
        else:
            course_create_form = CourseForm(request.POST)
            if course_create_form.is_valid():
                course = course_create_form.save(commit=False)
                if course.can_be_created():
                    course.save()
                    messages.success(request, 'Course has been created successfully.')
                    return redirect(reverse('CreateCoursePage'))
                else:
                    messages.error(request, 'The semester has either not started or has already ended.')

            courses = Course.objects.all().order_by("course_id")
            paginator = Paginator(courses, 5)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            return render(request, 'manager_courses.html', {'form': course_create_form, 'page_obj': page_obj})


@method_decorator(login_required, name="dispatch")
@method_decorator(user_is_manager, name="dispatch")
class AddUserView(View):
    def get(self, request):
        add_user_form = CreateUserForm()
        in_active_students = User.objects.filter(is_active=False).order_by('id')

        paginator = Paginator(in_active_students, 5)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'manager_users.html', {'form': add_user_form, 'page_obj': page_obj})

    def post(self, request):
        if "add_user" in request.POST:
            add_user_form = CreateUserForm(request.POST)
            if add_user_form.is_valid():
                id = add_user_form.cleaned_data.get('id')
                first_name = add_user_form.cleaned_data.get('first_name')
                last_name = add_user_form.cleaned_data.get('last_name')
                email = add_user_form.cleaned_data.get('email')
                user_type = add_user_form.cleaned_data.get('user_type')
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
                                                    last_name=last_name)

                    Profile.objects.create(user=user, user_type=user_type)
                    send_mail('Welcome to CIES',
                              f'Hello {user.first_name} {user.last_name},\n\nYour new password is: {password}',
                              'mehmetalpkaynar@gmail.com',
                              [email],
                              fail_silently=False)
                    messages.success(request, "The user has been successfully created.")

                return redirect(reverse("AddUserPage"))
            else:
                in_active_students = User.objects.filter(is_active=False).order_by('id')

                paginator = Paginator(in_active_students, 5)
                page_number = request.GET.get('page')
                page_obj = paginator.get_page(page_number)

        elif "enroll" in request.POST:
            add_user_form = CreateUserForm()
            selected_students = request.POST.get("selected_students")
            for student_id in selected_students.split(','):
                student = User.objects.get(pk=int(student_id))
                student.is_active = True
                student.save()

            return redirect(reverse("AddUserPage"))

        elif "delete" in request.POST:
            add_user_form = CreateUserForm()
            selected_students = request.POST.get("selected_students")
            for student_id in selected_students.split(','):
                student = User.objects.get(pk=int(student_id))
                student.delete()

            return redirect(reverse("AddUserPage"))

        else:
            add_user_form = CreateUserForm()

        in_active_students = User.objects.filter(is_active=False).order_by('id')

        paginator = Paginator(in_active_students, 5)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return render(request, 'manager_users.html', {'form': add_user_form, 'page_obj': page_obj})


@method_decorator(login_required, name="dispatch")
@method_decorator(user_is_manager, name="dispatch")
class SemesterCreateView(View):
    def get_holidays(self):
        current_year = timezone.now().year
        start_year = current_year
        end_year = current_year
        holidays_list = []

        for year in range(start_year, end_year + 1):
            tr_holidays = holidays.Turkey(years=year)
            for date, name in sorted(tr_holidays.items()):
                holidays_list.append((date, name))
        return holidays_list

    def get(self, request):
        form = SemesterForm()
        holidays_turkey = self.get_holidays()

        context = {
            'form': form,
            'holidays_turkey': holidays_turkey,
        }
        print(holidays_turkey)

        return render(request, 'manager_semester.html', context)

    def post(self, request):
        form = SemesterForm(request.POST)
        if form.is_valid():
            semester = form.save(commit=False)
            semester.save()
            messages.success(request, 'Semester has been created successfully.')
            return redirect(reverse('CreateSemesterPage'))

        return render(request, 'manager_semester.html', {'form': form})


@method_decorator(login_required, name="dispatch")
@method_decorator(user_is_manager, name="dispatch")
class CourseEditView(View):
    template_name = 'manager_edit_course.html'
    SectionFormSet = formset_factory(SectionForm, extra=0)
    section_formset_class = SectionFormSet

    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        sections = course.sections.all()

        initial_data_classroom = [{'classroom': section.Classroom or None} for section in sections]
        initial_data_instructors = [{'instructor': section.Instructor or None} for section in sections]

        section_formset = self.section_formset_class(initial=initial_data_classroom)

        for i, form in enumerate(section_formset):
            classroom = initial_data_classroom[i]['classroom']
            form.initial['Classroom'] = classroom
            instructors = initial_data_instructors[i]['instructor']
            form.initial['Instructor'] = instructors

        context = {
            'sections': sections,
            'section_formset': section_formset,
        }

        return render(request, self.template_name, context)

    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        sections = course.sections.all()
        sections_id = course.sections.values_list("pk", flat=True)
        sections_id_list = list(sections_id)
        section_formset = self.section_formset_class(request.POST)
        if section_formset.is_valid():
            for i, form in enumerate(section_formset):
                classroom = form.cleaned_data.get('Classroom')
                instructor = form.cleaned_data.get('Instructor')
                section_id = sections_id_list[i]
                Section.objects.filter(pk=section_id).update(Classroom=classroom, Instructor=instructor)
            course.is_active = True
            course.save()
            return redirect(reverse('CreateCoursePage'))

        context = {
            'sections': sections,
            'section_formset': section_formset,
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_is_manager, name="dispatch")
class ManagerLogoutView(View):
    def get(self, request):
        logout(request)

        return redirect(reverse("HomePage"))
