from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from accounts.models import Section, Profile, Transcript, Grade, Course, Semester
from announcements import get_announcements
from .forms import ChangeEmailForm, ChangePasswordForm
from django.db.models import Case, When, Value, BooleanField


def user_is_instructor(function):
    def wrap(request, *args, **kwargs):
        profile = Profile.objects.get(user=request.user)
        if profile.user_type == 'instructor':
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


@method_decorator(login_required, name="dispatch")
@method_decorator(user_is_instructor, name="dispatch")
class InstructorView(View):
    def get(self, request):
        cs_announcements = get_announcements()

        announcements_paginator_page = Paginator(cs_announcements, 4)
        announcements_page_number = request.GET.get('page')
        announcements_obj = announcements_paginator_page.get_page(announcements_page_number)

        current_date = timezone.now().date()
        semester = Semester.objects.filter(start_date__lte=current_date, finish_date__gte=current_date).first()

        total_length = semester.semester_length()
        elapsed_length = semester.elapsed_days()
        percentage_complete = min(100, max(0, (elapsed_length / total_length) * 100))

        context = {
            'announcements_obj': announcements_obj,
            'percentage_complete': percentage_complete,
            'semester': semester,
        }
        return render(request, "instructor_dashboard.html", context)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_is_instructor, name="dispatch")
class InstructorCoursesView(View):
    def get(self, request):
        instructor = User.objects.get(pk=request.user.pk)

        current_date = timezone.now().date()
        semester = Semester.objects.filter(start_date__lte=current_date, finish_date__gte=current_date).first()

        active_courses = Section.objects.filter(Instructor=instructor,
                                                course__semester=semester).order_by('course__course_id')
        enrolled_courses = Course.objects.filter(sections__Instructor=instructor).annotate(
            is_current_semester=Case(
                When(semester=semester, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        ).order_by("-is_current_semester", "course_id")

        paginator_active_page = Paginator(active_courses, 5)
        paginator_forum_page = Paginator(enrolled_courses, 8)

        active_page_number = request.GET.get('active_page')
        forum_page_number = request.GET.get('forum_page')

        active_page_obj = paginator_active_page.get_page(active_page_number)
        forum_page_obj = paginator_forum_page.get_page(forum_page_number)

        context = {
            'active_page_obj': active_page_obj,
            'forum_page_obj': forum_page_obj,
            'semester': semester,
        }

        return render(request, 'instructor_courses.html', context)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_is_instructor, name="dispatch")
class InstructorGradeView(View):
    def get(self, request, section_id):
        section = Section.objects.get(pk=section_id)
        students = section.students.all().order_by('id')

        for student in students:
            try:
                transcript = Transcript.objects.get(student=student)
                grade = Grade.objects.get(transcript=transcript, course=section.course)
                student.grade = grade.value
            except (Transcript.DoesNotExist, Grade.DoesNotExist):
                student.grade = None

        paginator_students_page = Paginator(students, 5)
        students_page_number = request.GET.get('page')
        students_page_obj = paginator_students_page.get_page(students_page_number)

        context = {
            'section': section,
            'students_page_obj': students_page_obj,
        }

        return render(request, 'instructor_grade.html', context)

    def post(self, request, section_id):
        section = Section.objects.get(pk=section_id)
        grades = request.POST.getlist('grades[]')
        student_ids = request.POST.getlist('student_ids[]')

        try:
            for student_id, grade in zip(student_ids, grades):
                if float(grade) < 0 or float(grade) > 100:
                    messages.success(request, "Grade should be between 0 and 100")
                    return redirect(reverse("InstructorGradesPage", args=section_id))
                student = Profile.objects.get(pk=student_id)

                transcript, created = Transcript.objects.get_or_create(student=student)

                if Grade.objects.filter(transcript=transcript,
                                        course=section.course,
                                        instructor=request.user,
                                        ):
                    grade_obj = Grade.objects.get(transcript=transcript,
                                                  course=section.course,
                                                  instructor=request.user,
                                                  )
                    grade_obj.value = float(grade)
                    grade_obj.save()
                else:
                    Grade.objects.create(
                        transcript=transcript,
                        course=section.course,
                        instructor=request.user,
                        value=float(grade))

            return redirect(reverse('InstructorCoursesPage'))
        except Exception as e:
            print(str(e))
            messages.success(request, "There is an error!")

        students = section.students.all().order_by('id')

        paginator_students_page = Paginator(students, 5)
        students_page_number = request.GET.get('page')
        students_page_obj = paginator_students_page.get_page(students_page_number)

        context = {
            'section': section,
            'students_page_obj': students_page_obj,
        }

        return render(request, 'instructor_grade.html', context)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_is_instructor, name="dispatch")
class InstructorAccountView(View):
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
                    if User.objects.filter(email=new_email_address).exists():
                        messages.success(request, "The email has already been taken!")
                    else:
                        request.user.email = new_email_address
                        request.user.save()
                        messages.success(request, 'The email has been changed successfully')
                else:
                    messages.success(request, 'The password is wrong!')

        else:
            password_form = ChangePasswordForm()
            email_form = ChangeEmailForm()

        return render(request, "instructor_account.html", {"password_form": password_form, 'email_form': email_form})


@method_decorator(login_required, name="dispatch")
@method_decorator(user_is_instructor, name="dispatch")
class InstructorLogoutView(View):
    def get(self, request):
        logout(request)

        return redirect(reverse("HomePage"))
