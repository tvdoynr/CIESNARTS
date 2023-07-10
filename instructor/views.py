from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from accounts.models import Section, Profile, Transcript, Grade
from .forms import ChangeEmailForm, ChangePasswordForm


@method_decorator(login_required, name="dispatch")
class InstructorView(View):
    def get(self, request):
        return render(request, "instructor_dashboard.html")


@method_decorator(login_required, name="dispatch")
class InstructorCoursesView(View):
    def get(self, request):
        instructor = User.objects.get(pk=request.user.pk)
        active_courses = Section.objects.filter(Instructor=instructor).order_by('course__CourseID')

        paginator_active_page = Paginator(active_courses, 5)
        paginator_forum_page = Paginator(active_courses, 5)

        active_page_number = request.GET.get('active_page')
        forum_page_number = request.GET.get('forum_page')

        active_page_obj = paginator_active_page.get_page(active_page_number)
        forum_page_obj = paginator_forum_page.get_page(forum_page_number)

        context = {
            'active_page_obj': active_page_obj,
            'forum_page_obj': forum_page_obj
        }

        return render(request, 'instructor_courses.html', context)


@method_decorator(login_required, name="dispatch")
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
                student = Profile.objects.get(pk=student_id)

                transcript, created = Transcript.objects.get_or_create(student=student)

                grade = Grade.objects.create(
                    transcript=transcript,
                    course=section.course,
                    instructor=request.user,
                    value=float(grade))
                grade.save()
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
                    request.user.email = new_email_address
                    request.user.save()
                    messages.success(request, 'The email has been changed successfully')
                else:
                    messages.success(request, 'The password is wrong!')

        else:
            password_form = ChangePasswordForm()
            email_form = ChangeEmailForm()

        return render(request, "instructor_account.html", {"password_form": password_form, 'email_form': email_form})
