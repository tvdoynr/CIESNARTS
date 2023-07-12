from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from accounts.models import Course, Section, Profile, Transcript, Grade
from .forms import ChangeEmailForm, ChangePasswordForm


@method_decorator(login_required, name="dispatch")
class StudentView(View):
    def get(self, request):

        return render(request, "student_dashboard.html")


@method_decorator(login_required, name="dispatch")
class StudentAccountView(View):
    def get(self, request):
        password_form = ChangePasswordForm()
        email_form = ChangeEmailForm()

        return render(request, "student_account.html", {"email_form": email_form,
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

        return render(request, "student_account.html", {"password_form": password_form, 'email_form': email_form})


@method_decorator(login_required, name="dispatch")
class StudentCourseView(View):
    def get(self, request):
        student = Profile.objects.get(user=request.user)
        active_courses = Course.objects.filter(is_active=True).order_by("CourseID")
        enrolled_courses = Course.objects.filter(sections__students=student).order_by("CourseID")

        active_courses = [course for course in active_courses if not course.is_student_enrolled(student)]

        paginator_enrolled_page = Paginator(enrolled_courses, 5)
        paginator_can_enroll_course = Paginator(active_courses, 5)

        enrolled_page_number = request.GET.get('enrolled_page')
        can_enroll_page_number = request.GET.get('can_enroll_page')

        enrolled_page_obj = paginator_enrolled_page.get_page(enrolled_page_number)
        can_enroll_page_obj = paginator_can_enroll_course.get_page(can_enroll_page_number)

        context = {
            'can_enroll_page_obj': can_enroll_page_obj,
            'enrolled_page_obj': enrolled_page_obj,
        }
        return render(request, 'student_courses.html', context)


@method_decorator(login_required, name="dispatch")
class StudentTakeCourseView(View):
    def get(self, request, course_id):
        course = Course.objects.get(pk=course_id)
        sections = course.sections.all()

        context = {
            'course': course,
            'sections': sections,
        }

        return render(request, "student_enroll_course.html", context)

    def post(self, request, course_id):
        section_id = request.POST.get('section_id')
        section = Section.objects.get(pk=section_id)
        if section.can_be_added():
            student = Profile.objects.get(user_id=request.user.id)
            section.students.add(student)
            section.NumberOfStudents += 1
            section.save()

            return redirect(reverse('StudentCoursePage'))

        course = Course.objects.get(pk=course_id)
        sections = course.sections.all()

        context = {
            'course': course,
            'sections': sections,
        }
        messages.success(request, "Section is full already!")
        return render(request, "student_enroll_course.html", context)


@method_decorator(login_required, name="dispatch")
class StudentTranscriptView(View):
    def get(self, request):
        student = Profile.objects.get(user=request.user)
        grades = Grade.objects.filter(transcript__student=student).order_by("course__CourseID")

        '''letter_grades = ["A1" if grade >= 95
                         else ("A2" if grade >= 90
                              else ("A3" if grade >= 85
                                   else ("B1" if grade >= 80
                                         else ("B2" if grade >= 75
                                               else ("B3" if grade >= 70
                                                     else ("C1" if grade >= 65
                                                           else ("C2" if grade >= 60
                                                                 else ("C3" if grade >= 55
                                                                       else ("D" if grade >= 50
                                                                             else "F")))))))))
                         for grade in grades]'''

        context = {
            'student': student,
            'grades': grades,
        }

        return render(request, 'student_transcript.html', context)


class StudentLogoutView(View):
    def get(self, request):
        logout(request)

        return redirect(reverse("HomePage"))
