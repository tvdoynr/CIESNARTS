from django.urls import path
from . import views

urlpatterns = [
    path("submissions/<int:course_id>/", views.SubmissionView.as_view(), name="SubmissionsPage"),
    path("submit/<int:course_id>/", views.SubmitView.as_view(), name="SubmitPage"),
    path("submissions/<int:course_id>/comments/<int:submission_id>/", views.CommentsView.as_view(), name="CommentsPage"),
    path("course/<int:course_id>/profile/<int:user_id>/", views.CieszaProfileView.as_view(), name="CieszaProfilePage"),
    path("course/<int:course_id>/profile/<int:user_id>/edit/", views.CieszaProfileEditView.as_view(), name="CieszaProfileEditPage"),
    path("submissions/<int:course_id>/search/", views.SearchSubmissionsView.as_view(), name="SubmissionsSearch"),

]
