from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View

from accounts.models import Course, Profile
from ciesza.models import Submission, Comment


class SubmissionView(View):
    def get(self, request, course_id):
        course = Course.objects.get(pk=course_id)
        submissions = course.submissions.all()

        paginator_submissions = Paginator(submissions, 20)
        submissions_page_number = request.GET.get('page')
        submissions_page_obj = paginator_submissions.get_page(submissions_page_number)

        context = {
            'course': course,
            'submissions_page_obj': submissions_page_obj,
            'course_id': course_id
        }

        return render(request, 'ciesza_submissions.html', context)


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


class CommentsView(View):
    def get(self, request, course_id, submission_id):
        comments = Comment.objects.filter(submission_id=submission_id, parent_id__isnull=True).order_by('-score')
        submission = Submission.objects.get(pk=submission_id)

        context = {
            'comments': comments,
            'submission': submission
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
