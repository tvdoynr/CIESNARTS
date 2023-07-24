from django.urls import path, include
from . import views

urlpatterns = [
    path("select2/", include("django_select2.urls")),
    path("", views.ManagerView.as_view(), name="ManagerPage"),
    path("account/", views.ManagerAccountView.as_view(), name="ManagerAccountPage"),
    path("courses/", views.CourseCreateView.as_view(), name="CreateCoursePage"),
    path("semester/", views.SemesterCreateView.as_view(), name="CreateSemesterPage"),
    path("users/", views.AddUserView.as_view(), name="AddUserPage"),
    path('course/<int:course_id>/edit/', views.CourseEditView.as_view(), name='edit_course'),
    path("logout/", views.ManagerLogoutView.as_view(), name="ManagerLogout")

]