from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import models
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from accounts.models import Course, Profile
from ciesza.forms import ChangeAuthorNameForm
from ciesza.models import Submission, Comment, Vote


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

        for submission in submissions:
            submission.up_voted = Vote.objects.filter(submission=submission, author__user=request.user,
                                                      up_vote=True).exists()
            submission.down_voted = Vote.objects.filter(submission=submission, author__user=request.user,
                                                        down_vote=True).exists()

        paginator_submissions = Paginator(submissions, 20)
        submissions_page_number = request.GET.get('page')
        submissions_page_obj = paginator_submissions.get_page(submissions_page_number)

        context = {
            'course': course,
            'submissions_page_obj': submissions_page_obj,
            'course_id': course_id
        }

        return render(request, 'ciesza_submissions.html', context)

    def post(self, request, course_id):
        print(request.POST)

        submission_id = request.POST.get("what_id")
        vote_type = request.POST.get("vote_type")
        author_id = request.POST.get("what_user")

        author = Profile.objects.get(user_id=author_id)
        submission = Submission.objects.get(pk=submission_id)

        vote, created = Vote.objects.get_or_create(submission_id=submission_id, author=author)
        vote_flag_up = vote.up_vote
        vote_flag_down = vote.down_vote

        if vote_type == 'up_vote':
            if vote_flag_up:
                vote.up_vote = False
                submission.score -= 1
            else:
                if vote_flag_down:
                    vote.down_vote = False
                    vote.up_vote = True
                    submission.score += 2
                else:
                    vote.up_vote = True
                    submission.score += 1
        else:
            if vote_flag_up:
                vote.down_vote = True
                vote.up_vote = False
                submission.score -= 2
            else:
                if vote_flag_down:
                    vote.down_vote = False
                    submission.score += 1
                else:
                    vote.down_vote = True
                    submission.score -= 1

        vote.save()
        submission.save()

        '''course = Course.objects.get(pk=course_id)
        submissions = course.submissions.all().order_by('-score')

        paginator_submissions = Paginator(submissions, 20)
        submissions_page_number = request.GET.get('page')
        submissions_page_obj = paginator_submissions.get_page(submissions_page_number)

        context = {
            'course': course,
            'submissions_page_obj': submissions_page_obj,
            'course_id': course_id,
        }'''

        new_score = submission.score
        return JsonResponse({'new_score': new_score})
        #return render(request, 'ciesza_submissions.html', context)


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

        submission.up_voted = Vote.objects.filter(submission=submission, author__user=request.user,
                                                  up_vote=True).exists()
        submission.down_voted = Vote.objects.filter(submission=submission, author__user=request.user,
                                                    down_vote=True).exists()

        for comment in comments:
            comment.up_voted = Vote.objects.filter(comment=comment, author__user=request.user,
                                                   up_vote=True).exists()
            comment.down_voted = Vote.objects.filter(comment=comment, author__user=request.user,
                                                     down_vote=True).exists()

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

        elif "reply" in request.POST:
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

        else:
            submission_comment_id = request.POST.get("what_id")
            vote_type = request.POST.get("vote_type")
            author_id = request.POST.get("what_user")
            submission_comment_type = request.POST.get("what_type")

            author = Profile.objects.get(user_id=author_id)

            if submission_comment_type == "submission":
                print(request.POST)
                print("1")
                submission = Submission.objects.get(pk=submission_comment_id)

                vote, created = Vote.objects.get_or_create(submission_id=submission_comment_id, author=author)
                vote_flag_up = vote.up_vote
                vote_flag_down = vote.down_vote

                if vote_type == 'up_vote':
                    if vote_flag_up:
                        vote.up_vote = False
                        submission.score -= 1
                    else:
                        if vote_flag_down:
                            vote.down_vote = False
                            vote.up_vote = True
                            submission.score += 2
                        else:
                            vote.up_vote = True
                            submission.score += 1
                else:
                    if vote_flag_up:
                        vote.down_vote = True
                        vote.up_vote = False
                        submission.score -= 2
                    else:
                        if vote_flag_down:
                            vote.down_vote = False
                            submission.score += 1
                        else:
                            vote.down_vote = True
                            submission.score -= 1

                vote.save()
                submission.save()
                new_score = submission.score
            else:
                print(request.POST)
                print("2")
                comment = Comment.objects.get(pk=submission_comment_id)

                vote, created = Vote.objects.get_or_create(comment_id=submission_comment_id, author=author)
                vote_flag_up = vote.up_vote
                vote_flag_down = vote.down_vote

                if vote_type == 'up_vote':
                    if vote_flag_up:
                        vote.up_vote = False
                        comment.score -= 1
                    else:
                        if vote_flag_down:
                            vote.down_vote = False
                            vote.up_vote = True
                            comment.score += 2
                        else:
                            vote.up_vote = True
                            comment.score += 1
                else:
                    if vote_flag_up:
                        vote.down_vote = True
                        vote.up_vote = False
                        comment.score -= 2
                    else:
                        if vote_flag_down:
                            vote.down_vote = False
                            comment.score += 1
                        else:
                            vote.down_vote = True
                            comment.score -= 1

                vote.save()
                comment.save()
                new_score = comment.score

            return JsonResponse({'new_score': new_score})

        return redirect(reverse('CommentsPage', args=(course_id, submission_id)))


@method_decorator(login_required, name="dispatch")
@method_decorator(user_has_role('student', 'instructor'), name='dispatch')
class CieszaProfileView(View):
    def get(self, request, course_id, user_id):
        author = Profile.objects.get(user_id=user_id)
        submissions = Submission.objects.filter(author=author, course_id=course_id).order_by('-score')

        for submission in submissions:
            submission.up_voted = Vote.objects.filter(submission=submission, author__user=request.user,
                                                      up_vote=True).exists()
            submission.down_voted = Vote.objects.filter(submission=submission, author__user=request.user,
                                                        down_vote=True).exists()

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

        total_score = author_submission_score + author_comment_score
        user_id = user_id

        author.score = total_score
        context = {
            'submissions_page_obj': submissions_page_obj,
            'course_id': course_id,
            'author': author,
            'courses': courses,
            'user_id': user_id,
        }

        return render(request, 'ciesza_profile.html', context)

    def post(self, request, course_id, user_id):
        print(request.POST)

        submission_id = request.POST.get("what_id")
        vote_type = request.POST.get("vote_type")
        author_id = request.POST.get("what_user")

        author = Profile.objects.get(user_id=author_id)
        submission = Submission.objects.get(pk=submission_id)

        vote, created = Vote.objects.get_or_create(submission_id=submission_id, author=author)
        vote_flag_up = vote.up_vote
        vote_flag_down = vote.down_vote

        if vote_type == 'up_vote':
            if vote_flag_up:
                vote.up_vote = False
                submission.score -= 1
            else:
                if vote_flag_down:
                    vote.down_vote = False
                    vote.up_vote = True
                    submission.score += 2
                else:
                    vote.up_vote = True
                    submission.score += 1
        else:
            if vote_flag_up:
                vote.down_vote = True
                vote.up_vote = False
                submission.score -= 2
            else:
                if vote_flag_down:
                    vote.down_vote = False
                    submission.score += 1
                else:
                    vote.down_vote = True
                    submission.score -= 1

        vote.save()
        submission.save()

        new_score = submission.score

        author_submission_score = Submission.objects.filter(author=author).aggregate(models.Sum('score'))['score__sum']
        author_comment_score = Comment.objects.filter(author=author).aggregate(models.Sum('score'))['score__sum']

        if author_submission_score is None:
            author_submission_score = 0
        if author_comment_score is None:
            author_comment_score = 0

        total_score = author_submission_score + author_comment_score
        author.score = total_score

        return JsonResponse({
            'new_score': new_score,
            'author_score': author.score})


@method_decorator(login_required, name="dispatch")
@method_decorator(user_has_role('student', 'instructor'), name='dispatch')
class CieszaProfileEditView(View):
    def get(self, request, course_id, user_id):
        author_name_form = ChangeAuthorNameForm()

        context = {
            'author_name_form': author_name_form,
            'course_id': course_id,
            'user_id': user_id,
        }

        return render(request, 'ciesza_edit_profile.html', context)

    def post(self, request, course_id, user_id):
        author_name_form = ChangeAuthorNameForm(request.POST)
        if author_name_form.is_valid():
            author_name = author_name_form.cleaned_data.get("author_name")
            confirm_password = author_name_form.cleaned_data.get("confirm_password")

            user = authenticate(request, username=request.user.username, password=confirm_password)

            if user is not None:
                author = Profile.objects.get(user=user)
                Submission.objects.filter(author=author).update(author_name=author_name)
                Comment.objects.filter(author=author).update(author_name=author_name)
                messages.success(request, "The author name has been changed successfully!")
            else:
                messages.success(request, "The password is invalid!")

        context = {
            'author_name_form': author_name_form,
            'course_id': course_id,
            'user_id': user_id,
        }

        return render(request, 'ciesza_edit_profile.html', context)
