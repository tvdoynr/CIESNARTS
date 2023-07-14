from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import models
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from accounts.models import Course, Profile
from ciesza.forms import ChangeAuthorNameForm
from ciesza.models import Submission, Comment


def user_has_role(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            profile = Profile.objects.get(user=request.user)
            if profile.user_type in roles:
                return view_func(request, *args, **kwargs)
            else:
                raise PermissionDenied

        return _wrapped_view

    return decorator


@method_decorator(login_required, name="dispatch")
@method_decorator(user_has_role("student", "instructor"), name='dispatch')
class SubmissionView(View):
    def get(self, request, course_id):
        course = Course.objects.get(pk=course_id)
        submissions = course.submissions.all().order_by('-score')

        paginator_submissions = Paginator(submissions, 20)
        submissions_page_number = request.GET.get('page')
        submissions_page_obj = paginator_submissions.get_page(submissions_page_number)

        context = {
            'course': course,
            'submissions_page_obj': submissions_page_obj,
            'course_id': course_id
        }

        return render(request, 'ciesza_submissions.html', context)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_has_role("student", "instructor"), name="dispatch")
class SubmitView(View):
    def get(self, request, course_id):
        context = {
            'course_id': course_id,
        }

        return render(request, 'ciesza_submit.html', context)

    def post(self, request, course_id):
        title = request.POST.get('title')
        text = request.POST.get('text')

        course = Course.objects.get(pk=course_id)
        author = Profile.objects.get(user=request.user)

        submission = Submission.objects.create(
            course=course,
            author=author,
            author_name=author.user_id,
            title=title,
            text=text,
        )
        submission.save()

        return redirect(reverse('SubmissionsPage', args=course_id))


@method_decorator(login_required, name="dispatch")
@method_decorator(user_has_role("student", "instructor"), name="dispatch")
class CommentsView(View):
    def get(self, request, course_id, submission_id):
        comments = Comment.objects.filter(submission_id=submission_id, parent_id__isnull=True).order_by('-score')
        submission = Submission.objects.get(pk=submission_id)

        context = {
            'comments': comments,
            'submission': submission,
            'course_id': course_id,
        }

        return render(request, 'ciesza_comments.html', context)

    def post(self, request, course_id, submission_id):
        if "comment" in request.POST:
            text = request.POST.get('text')
            submission = Submission.objects.get(pk=submission_id)
            author = Profile.objects.get(user=request.user)

            comment = Comment.objects.create(
                submission=submission,
                author=author,
                author_name=author.user_id,
                text=text
            )
            comment.save()
            submission.comment_count += 1
            submission.save()

        if "reply" in request.POST:
            text = request.POST.get('text')
            parent_id = request.POST.get('parent_comment')
            submission = Submission.objects.get(pk=submission_id)
            author = Profile.objects.get(user=request.user)
            parent_comment = Comment.objects.get(pk=parent_id)

            comment = Comment.objects.create(
                submission=submission,
                author=author,
                author_name=author.user_id,
                text=text,
                parent=parent_comment
            )
            comment.save()
            submission.comment_count += 1
            submission.save()

        return redirect(reverse('CommentsPage', args=(course_id, submission_id)))


@method_decorator(login_required, name="dispatch")
@method_decorator(user_has_role('student', 'instructor'), name='dispatch')
class CieszaProfileView(View):
    def get(self, request, course_id, user_id):
        author = Profile.objects.get(user_id=user_id)
        submissions = Submission.objects.filter(author=author, course_id=course_id).order_by('-score')
        sections = author.enrolled_sections.all()

        courses = [section.course for section in sections]

        paginator_submissions = Paginator(submissions, 10)
        submissions_page = request.GET.get('page')
        submissions_page_obj = paginator_submissions.get_page(submissions_page)

        author_submission_score = Submission.objects.filter(author=author).aggregate(models.Sum('score'))['score__sum']
        author_comment_score = Comment.objects.filter(author=author).aggregate(models.Sum('score'))['score__sum']

        if author_submission_score is None:
            author_submission_score = 0
        if author_comment_score is None:
            author_comment_score = 0

        score = author_submission_score + author_comment_score
        user_id = user_id

        author.score = score
        context = {
            'submissions_page_obj': submissions_page_obj,
            'course_id': course_id,
            'author': author,
            'courses': courses,
            'user_id': user_id,
        }

        return render(request, 'ciesza_profile.html', context)


class CieszaProfileEditView(View):
    def get(self, request, course_id, user_id):
        author_name_form = ChangeAuthorNameForm()

        context = {
            'author_name_form': author_name_form,
            'course_id': course_id,
            'user_id': user_id,
        }

        return render(request, 'ciesza_edit_profile.html', context)


