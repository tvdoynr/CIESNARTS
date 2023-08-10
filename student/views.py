import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.files.images import ImageFile
from django.core.paginator import Paginator
from django.db.models import F, Case, When, Value, BooleanField
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from announcements import get_announcements
from django.db import transaction
from accounts.models import Course, Section, Profile, Grade, Semester, Image
from .decorators import user_is_student
from .forms import ChangeEmailForm, ChangePasswordForm, ProfileForm


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

        if semester is None:
            semester = Semester.objects.filter(finish_date__lte=current_date).last()
            if semester is None:
                context = {
                    'announcements_obj': announcements_obj,
                    'semester': semester,
                }

                return render(request, "student_dashboard.html", context)

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
        profile_form = ProfileForm()

        context = {
            "email_form": email_form,
            "password_form": password_form,
            'profile_form': profile_form,
        }

        return render(request, "student_account.html", context)

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

        return render(request, "student_account.html", {"password_form": password_form,
                                                        'email_form': email_form,
                                                        'profile_form': profile_form})


@method_decorator(login_required, name="dispatch")
@method_decorator(user_is_student, name="dispatch")
class StudentCourseView(View):
    def get(self, request):
        student = Profile.objects.get(user=request.user)

        current_date = timezone.now().date()
        semester = Semester.objects.filter(start_date__lte=current_date, finish_date__gte=current_date).first()

        active_courses = Course.objects.filter(is_active=True, semester=semester).exclude(sections__students=student).order_by("course_id")
        enrolled_courses = Course.objects.filter(sections__students=student).annotate(
            is_current_semester=Case(
                When(semester=semester, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        ).order_by("-is_current_semester", "course_id")

        #active_courses = [course for course in active_courses if not course.is_student_enrolled(student)]

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
                                                      instructor=section.instructor).exclude(course__semester=semester)

        grade_to_letter = {
            95: 0, 90: 1, 85: 2,
            80: 3, 75: 4, 70: 5,
            65: 6, 60: 7, 55: 8,
            50: 9, 0: 10
        }

        bins = {}
        for section_id, grade_values in grades.items():
            bins[section_id] = [0] * 11
            for grade_value in grade_values:
                for grade, index in grade_to_letter.items():
                    if grade_value.value >= grade:
                        bins[section_id][index] += 1
                        break

        context = {
            'course': course,
            'sections': sections,
            'bins': json.dumps(bins),
        }

        return render(request, "student_enroll_course.html", context)

    @transaction.atomic
    def post(self, request, course_id):
        section_id = request.POST.get('section_id')
        section = Section.objects.get(pk=section_id)
        if section.can_be_added():
            student = Profile.objects.get(user_id=request.user.id)
            section.students.add(student)
            section.number_of_students += 1
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
    def convert_grades(self, request, grades, check_flag):
        letter_to_gpa = {
            'A1': 4.0, 'A2': 3.75, 'A3': 3.50,
            'B1': 3.25, 'B2': 3.0, 'B3': 2.75,
            'C1': 2.50, 'C2': 2.25, 'C3': 2.0,
            'D': 1.75, 'F': 0.0
        }

        grade_to_letter = {
            95: 'A1', 90: 'A2', 85: 'A3',
            80: 'B1', 75: 'B2', 70: 'B3',
            65: 'C1', 60: 'C2', 55: 'C3',
            50: 'D', 0: 'F'
        }

        grades_credits = 0
        grades_x_credits = 0

        all_grade = []
        letter_grade = 'F'
        for grade in grades:
            for key_grade, item_letter in grade_to_letter.items():
                if grade.value >= key_grade:
                    letter_grade = item_letter
                    break
            grades_credits += grade.course_credit
            grades_x_credits += letter_to_gpa[letter_grade] * grade.course_credit
            all_grade.append(letter_grade)

        try:
            gpa = round(grades_x_credits / grades_credits, 2)
        except ZeroDivisionError:
            gpa = 0

        if check_flag:
            return gpa

        return [gpa, zip(grades, all_grade)]

    def get(self, request):
        student = Profile.objects.get(user=request.user)

        current_date = timezone.now().date()
        semester = Semester.objects.filter(start_date__lte=current_date, finish_date__gte=current_date).first()

        semesters = Semester.objects.all()

        semester_grades = Grade.objects.filter(transcript__student=student, course__semester=semester).annotate(
            course_credit=F('course__course_credit')).order_by("course__course_id")

        total_grades = Grade.objects.filter(transcript__student=student).annotate(
            course_credit=F('course__course_credit'))

        result = self.convert_grades(request, semester_grades, False)
        semester_gpa = result[0]
        semester_final_grades = result[1]

        total_gpa = self.convert_grades(request, total_grades, True)

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

        result = self.convert_grades(request, semester_grades, False)
        semester_gpa = result[0]
        final_grades = result[1]

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
