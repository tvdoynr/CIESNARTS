from django.urls import path
from . import views

urlpatterns = [
    path("", views.InstructorView.as_view(), name="InstructorPage"),
    path("courses/", views.InstructorCoursesView.as_view(), name="InstructorCoursesPage"),
    path("section/<int:section_id>/grades/", views.InstructorGradeView.as_view(), name="InstructorGradesPage"),
    path("account/", views.InstructorAccountView.as_view(), name="InstructorAccountPage"),
    path("logout/", views.InstructorLogoutView.as_view(), name="InstructorLogout")

]
