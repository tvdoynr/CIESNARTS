from django.urls import path
from . import views

urlpatterns = [
    path("submissions/<int:course_id>/", views.SubmissionView.as_view(), name="SubmissionsPage"),
    path("submit/<int:course_id>/", views.SubmitView.as_view(), name="SubmitPage"),
    path("submissions/<int:course_id>/comments/<int:submission_id>/", views.CommentsView.as_view(), name="CommentsPage"),
]
