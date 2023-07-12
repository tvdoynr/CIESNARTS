from django.shortcuts import redirect
from django.urls import path, reverse_lazy, reverse
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("", views.StudentView.as_view(), name="StudentPage"),
    path("courses/", views.StudentCourseView.as_view(), name="StudentCoursePage"),
    path("course/<int:course_id>/enroll/", views.StudentTakeCourseView.as_view(), name="StudentTakeCoursePage"),
    path("transcript/", views.StudentTranscriptView.as_view(), name="StudentTranscriptPage"),
    path("account/", views.StudentAccountView.as_view(), name="StudentAccountPage"),
    path("logout/", views.StudentLogoutView.as_view(), name="StudentLogout")
]
