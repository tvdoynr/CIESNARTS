from django.urls import path
from . import views

urlpatterns = [
    path("", views.InstructorView.as_view(), name="InstructorPage"),
    path("account/", views.InstructorAccountView.as_view(), name="InstructorAccountPage")
]