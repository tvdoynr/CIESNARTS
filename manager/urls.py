from django.urls import path
from . import views

urlpatterns = [
    path("", views.ManagerView.as_view(), name="ManagerPage"),
    path("account/", views.ManagerAccountView.as_view(), name="ManagerAccountPage"),
    path("courses/", views.CourseCreateView.as_view(), name="CreateCoursePage"),
    path("semester/", views.SemesterCreateView.as_view(), name="CreateSemesterPage"),
]