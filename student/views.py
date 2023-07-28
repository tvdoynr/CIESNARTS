import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import F, Case, When, Value, BooleanField
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from announcements import get_announcements

from accounts.models import Course, Section, Profile, Grade, Semester
from .forms import ChangeEmailForm, ChangePasswordForm


def user_is_student(function):
    def wrap(request, *args, **kwargs):
        profile = Profile.objects.get(user=request.user)
        if profile.user_type == 'student':
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


@method_decorator(login_required, name="dispatch")
@method_decorator(user_is_student, name="dispatch")
class StudentView(View):
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

        return render(request, "student_dashboard.html", context)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_is_student, name="dispatch")
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
@method_decorator(user_is_student, name="dispatch")
class StudentCourseView(View):
    def get(self, request):
        student = Profile.objects.get(user=request.user)

        current_date = timezone.now().date()
        semester = Semester.objects.filter(start_date__lte=current_date, finish_date__gte=current_date).first()

        active_courses = Course.objects.filter(is_active=True, semester=semester).order_by("course_id")
        enrolled_courses = Course.objects.filter(sections__students=student).annotate(
            is_current_semester=Case(
                When(semester=semester, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        ).order_by("-is_current_semester", "course_id")

        active_courses = [course for course in active_courses if not course.is_student_enrolled(student)]

        paginator_enrolled_page = Paginator(enrolled_courses, 8)
        paginator_can_enroll_course = Paginator(active_courses, 5)

        enrolled_page_number = request.GET.get('enrolled_page')
        can_enroll_page_number = request.GET.get('can_enroll_page')

        enrolled_page_obj = paginator_enrolled_page.get_page(enrolled_page_number)
        can_enroll_page_obj = paginator_can_enroll_course.get_page(can_enroll_page_number)

        context = {
            'can_enroll_page_obj': can_enroll_page_obj,
            'enrolled_page_obj': enrolled_page_obj,
            'semester': semester,
        }
        return render(request, 'student_courses.html', context)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_is_student, name="dispatch")
class StudentTakeCourseView(View):
    def get(self, request, course_id):
        course = Course.objects.get(pk=course_id)
        sections = course.sections.all()

        current_date = timezone.now().date()
        semester = Semester.objects.filter(start_date__lte=current_date, finish_date__gte=current_date).first()

        grades = {}
        for section in sections:
            grades[section.id] = Grade.objects.filter(course__course_id=course.course_id,
                                                      instructor=section.Instructor).exclude(course__semester=semester)

        print(grades)
        bins = {}
        for section_id, grade_values in grades.items():
            bins[section_id] = [0] * 11
            for grade_value in grade_values:
                if grade_value.value >= 95:
                    bins[section_id][0] += 1
                elif grade_value.value >= 90:
                    bins[section_id][1] += 1
                elif grade_value.value >= 85:
                    bins[section_id][2] += 1
                elif grade_value.value >= 80:
                    bins[section_id][3] += 1
                elif grade_value.value >= 75:
                    bins[section_id][4] += 1
                elif grade_value.value >= 70:
                    bins[section_id][5] += 1
                elif grade_value.value >= 65:
                    bins[section_id][6] += 1
                elif grade_value.value >= 60:
                    bins[section_id][7] += 1
                elif grade_value.value >= 55:
                    bins[section_id][8] += 1
                elif grade_value.value >= 50:
                    bins[section_id][9] += 1
                else:
                    bins[section_id][10] += 1

        bins_list = [(k, v) for k, v in bins.items()]

        context = {
            'course': course,
            'sections': sections,
            'bin_list': bins_list,
            'bins': json.dumps(bins),
        }

        print(bins)

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
@method_decorator(user_is_student, name="dispatch")
class StudentTranscriptView(View):
    def get(self, request):
        student = Profile.objects.get(user=request.user)

        current_date = timezone.now().date()
        semester = Semester.objects.filter(start_date__lte=current_date, finish_date__gte=current_date).first()

        print(semester)
        semesters = Semester.objects.all()

        semester_grades = Grade.objects.filter(transcript__student=student, course__semester=semester).annotate(
            course_credit=F('course__course_credit')).order_by("course__course_id")

        total_grades = Grade.objects.filter(transcript__student=student).annotate(
            course_credit=F('course__course_credit'))

        letter_to_gpa = {
            'A1': 4.0, 'A2': 3.75, 'A3': 3.50,
            'B1': 3.25, 'B2': 3.0, 'B3': 2.75,
            'C1': 2.50, 'C2': 2.25, 'C3': 2.0,
            'D': 1.75, 'F': 0.0
        }

        semester_credits = 0
        semester_grades_x_credits = 0

        all_grade = []
        for grade in semester_grades:
            letter_grade = "A1" if grade.value >= 95 else (
                "A2" if grade.value >= 90 else (
                    "A3" if grade.value >= 85 else (
                        "B1" if grade.value >= 80 else (
                            "B2" if grade.value >= 75 else (
                                "B3" if grade.value >= 70 else (
                                    "C1" if grade.value >= 65 else (
                                        "C2" if grade.value >= 60 else (
                                            "C3" if grade.value >= 55 else (
                                                "D" if grade.value >= 50 else "F"
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
            semester_credits += grade.course_credit
            semester_grades_x_credits += letter_to_gpa[letter_grade] * grade.course_credit
            all_grade.append(letter_grade)

        semester_final_grades = zip(semester_grades, all_grade)

        try:
            semester_gpa = round(semester_grades_x_credits / semester_credits, 2)
        except ZeroDivisionError:
            semester_gpa = 0

        total_credits = 0
        total_grades_x_credits = 0

        for grade in total_grades:
            letter_grade = "A1" if grade.value >= 95 else (
                "A2" if grade.value >= 90 else (
                    "A3" if grade.value >= 85 else (
                        "B1" if grade.value >= 80 else (
                            "B2" if grade.value >= 75 else (
                                "B3" if grade.value >= 70 else (
                                    "C1" if grade.value >= 65 else (
                                        "C2" if grade.value >= 60 else (
                                            "C3" if grade.value >= 55 else (
                                                "D" if grade.value >= 50 else "F"
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
            total_credits += grade.course_credit
            total_grades_x_credits += letter_to_gpa[letter_grade] * grade.course_credit

        try:
            total_gpa = round(total_grades_x_credits / total_credits, 2)
        except ZeroDivisionError:
            total_gpa = 0

        context = {
            'student': student,
            'semester_final_grades': semester_final_grades,
            'semester': semester,
            'semesters': semesters,
            'semester_gpa': semester_gpa,
            'total_gpa': total_gpa,
            'default_semester_id': semester.id,
        }

        return render(request, 'student_transcript.html', context)

    def post(self, request):
        semester_id = request.POST.get("semester_id")
        semester = Semester.objects.get(pk=semester_id)
        student = Profile.objects.get(user=request.user)

        semester_grades = Grade.objects.filter(transcript__student=student, course__semester=semester).annotate(
            course_credit=F('course__course_credit')).order_by("course__course_id")

        letter_to_gpa = {
            'A1': 4.0, 'A2': 3.75, 'A3': 3.50,
            'B1': 3.25, 'B2': 3.0, 'B3': 2.75,
            'C1': 2.50, 'C2': 2.25, 'C3': 2.0,
            'D': 1.75, 'F': 0.0
        }

        semester_credits = 0
        semester_grades_x_credits = 0

        all_grade = []
        for grade in semester_grades:
            letter_grade = "A1" if grade.value >= 95 else (
                "A2" if grade.value >= 90 else (
                    "A3" if grade.value >= 85 else (
                        "B1" if grade.value >= 80 else (
                            "B2" if grade.value >= 75 else (
                                "B3" if grade.value >= 70 else (
                                    "C1" if grade.value >= 65 else (
                                        "C2" if grade.value >= 60 else (
                                            "C3" if grade.value >= 55 else (
                                                "D" if grade.value >= 50 else "F"
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
            semester_credits += grade.course_credit
            semester_grades_x_credits += letter_to_gpa[letter_grade] * grade.course_credit
            all_grade.append(letter_grade)

        final_grades = zip(semester_grades, all_grade)

        try:
            semester_gpa = round(semester_grades_x_credits / semester_credits, 2)
        except ZeroDivisionError:
            semester_gpa = 0

        grades_list = []
        for grade, letter_grade in final_grades:
            grades_list.append({
                'course_id': grade.course.course_id,
                'instructor': f"{grade.instructor.first_name} {grade.instructor.last_name}",
                'letter_grade': letter_grade,
                'course_credit': grade.course_credit,
                'semester_gpa': semester_gpa,
            })
        context = {
            'semester_final_grades': grades_list,
            'semester_gpa': semester_gpa,
        }

        return JsonResponse(context)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_is_student, name="dispatch")
class StudentLogoutView(View):
    def get(self, request):
        logout(request)

        return redirect(reverse("HomePage"))
