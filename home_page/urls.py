from django.urls import path
from . import views

urlpatterns = [
    path("", views.Homeview.as_view(), name="HomePage"),
    path("register/", views.RegistrationView.as_view(), name="RegisterPage"),
    path("forgotpassword/", views.ForgotPasswordView.as_view(), name="Forgotpassword")
]
