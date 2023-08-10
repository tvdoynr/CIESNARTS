import json

import holidays
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.files.images import ImageFile
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Avg, ProtectedError, Value, Count
from django.db.models.functions import Concat
from django.forms import formset_factory
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.views import View

from announcements import get_announcements
from .decorators import user_is_manager
from .forms import ChangeEmailForm, ChangePasswordForm, CourseForm, SemesterForm, CreateUserForm, SectionForm, \
    ProfileForm
from accounts.models import Course, Profile, Semester, Section, Grade, Image


@method_decorator(login_required, name="dispatch")
@method_decorator(user_is_manager, name="dispatch")
class ManagerView(View):
    def get(self, request):
        cs_announcements = get_announcements()

        announcements_paginator_page = Paginator(cs_announcements, 4)
        announcements_page_number = request.GET.get('page')
        announcements_obj = announcements_paginator_page.get_page(announcements_page_number)

        current_date = timezone.now().date()
        semester = Semester.objects.filter(start_date__lte=current_date, finish_date__gte=current_date).first()

        if semester is None:
            semester = Semester.objects.filter(finish_date__lte=current_date).last()
            if semester is None:
                context = {
                    'announcements_obj': announcements_obj,
                    'semester': semester,
                }

                return render(request, "manager_dashboard.html", context)

        total_length = semester.semester_length()
        elapsed_length = semester.elapsed_days()
        percentage_complete = min(100, max(0, (elapsed_length / total_length) * 100))

        students_count = Profile.objects.filter(user_type='student').count()
        instructor_count = Profile.objects.filter(user_type='instructor').count()
        course_count = Course.objects.filter(semester=semester).count()

        context = {
            'announcements_obj': announcements_obj,
            'percentage_complete': percentage_complete,
            'semester': semester,
            'students_count': students_count,
            'instructor_count': instructor_count,
            'course_count': course_count,
        }
        return render(request, "manager_dashboard.html", context)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_is_manager, name="dispatch")
class ManagerAccountView(View):
    def get(self, request):
        password_form = ChangePasswordForm()
        email_form = ChangeEmailForm()
        profile_form = ProfileForm()

        context = {
            "email_form": email_form,
            "password_form": password_form,
            'profile_form': profile_form,
        }

        return render(request, "manager_account.html", context)

    def post(self, request):
        if "password" in request.POST:
            password_form = ChangePasswordForm(request.POST)
            email_form = ChangeEmailForm()
            profile_form = ProfileForm()
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
            profile_form = ProfileForm()
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

        elif "profile" in request.POST:
            profile_form = ProfileForm(request.POST, request.FILES)
            password_form = ChangePasswordForm()
            email_form = ChangeEmailForm()

            if profile_form.is_valid():
                image_file = profile_form.cleaned_data['profile_picture']

                try:
                    img_obj = Image.objects.get(image=image_file.name)
                except Image.DoesNotExist:
                    img_obj = Image(image=ImageFile(image_file))
                    img_obj.save()

                request.user.profile.profile_picture = img_obj
                request.user.profile.save()
                messages.success(request, 'The profile picture has been changed successfully')

        else:
            password_form = ChangePasswordForm()
            email_form = ChangeEmailForm()
            profile_form = ProfileForm()

        return render(request, "manager_account.html", {"password_form": password_form,
                                                        'email_form': email_form,
                                                        'profile_form': profile_form})


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
        semesters = Semester.objects.all()

        context = {
            'form': form,
            'holidays_turkey': holidays_turkey,
            'semesters': semesters,
        }

        return render(request, 'manager_semester.html', context)

    def post(self, request):
        if "delete_semester" in request.POST:
            semester_id = request.POST.get("delete_semester")
            semester = get_object_or_404(Semester, id=semester_id)
            try:
                semester.delete()
                messages.success(request, 'Semester has been deleted successfully.')
                return redirect(reverse('CreateSemesterPage'))
            except ProtectedError:
                form = SemesterForm()
                messages.success(request, 'Delete the semesters course first!!!')
                holidays_turkey = self.get_holidays()
                semesters = Semester.objects.all()

                context = {
                    'form': form,
                    'holidays_turkey': holidays_turkey,
                    'semesters': semesters,
                }

                return render(request, 'manager_semester.html', context)

        form = SemesterForm(request.POST)
        if form.is_valid():
            semester = form.save(commit=False)
            semester.save()
            messages.success(request, 'Semester has been created successfully.')
            return redirect(reverse('CreateSemesterPage'))

        holidays_turkey = self.get_holidays()
        semesters = Semester.objects.all()

        context = {
            'form': form,
            'holidays_turkey': holidays_turkey,
            'semesters': semesters,
        }

        return render(request, 'manager_semester.html', context)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_is_manager, name="dispatch")
class CourseEditView(View):
    template_name = 'manager_edit_course.html'
    SectionFormSet = formset_factory(SectionForm, extra=0)
    section_formset_class = SectionFormSet

    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        sections = course.sections.all()

        current_date = timezone.now().date()
        past_semesters = Semester.objects.filter(finish_date__lt=current_date)

        past_courses = Course.objects.filter(course_id=course.course_id, semester__in=past_semesters)

        grades = Grade.objects.filter(course__in=past_courses).annotate(
            instructor_name=Concat('instructor__first_name', Value(' '), 'instructor__last_name'),
        ).values('instructor_name').annotate(
            avg_grade=Avg('value'),
            count=Count('value')
        ).order_by('-count')

        instructors = []
        avg_grades = []
        counts = []
        for grade in grades:
            instructors.append(grade['instructor_name'])
            avg_grades.append(grade['avg_grade'])
            counts.append(grade['count'])

        initial_data_classroom = [{'classroom': section.classroom or None} for section in sections]
        initial_data_instructors = [{'instructor': section.instructor or None} for section in sections]

        section_formset = self.section_formset_class(initial=initial_data_classroom)

        for i, form in enumerate(section_formset):
            classroom = initial_data_classroom[i]['classroom']
            form.initial['classroom'] = classroom
            instructors = initial_data_instructors[i]['instructor']
            form.initial['instructor'] = instructors

        context = {
            'course': course,
            'sections': sections,
            'section_formset': section_formset,
            'instructors': instructors,
            'avg_grades': avg_grades,
            'counts': counts,
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
                classroom = form.cleaned_data.get('classroom')
                instructor = form.cleaned_data.get('instructor')
                section_id = sections_id_list[i]
                Section.objects.filter(pk=section_id).update(classroom=classroom, instructor=instructor)
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
