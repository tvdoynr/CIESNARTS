from django.urls import path
from . import views

urlpatterns = [
    path("", views.StudentView.as_view(), name="StudentPage"),
    path("courses/", views.StudentCourseView.as_view(), name="StudentCoursePage"),
    path("course/<int:course_id>/enroll/", views.StudentTakeCourseView.as_view(), name="StudentTakeCoursePage"),
    path("account/", views.StudentAccountView.as_view(), name="StudentAccountPage")
]