from django.urls import path
from . import views

urlpatterns = [
    path("", views.StudentView.as_view(), name="StudentPage"),
    path("account/", views.StudentAccountView.as_view(), name="StudentAccountPage")
]