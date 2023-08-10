from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q, Value, Case, When, BooleanField
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from accounts.models import Course, Profile, Semester, Section
from ciesza.decorators import user_has_role
from ciesza.forms import ChangeAuthorNameForm
from ciesza.models import Submission, Comment, Vote


@method_decorator(login_required, name="dispatch")
@method_decorator(user_has_role("student", "instructor"), name='dispatch')
class SubmissionView(View):
    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)

        if not course.is_student_enrolled(request.user.profile) and request.user.profile.user_type == 'student':
            return HttpResponseForbidden("You do not have access to this course.")

        if request.user.profile.user_type == 'instructor':
            check_flag = Section.objects.filter(course=course, instructor=request.user).exists()
            if not check_flag:
                return HttpResponseForbidden("You do not have access to this course.")

        submissions = course.submissions.all().order_by('-score')

        up_votes = Vote.objects.filter(
            Q(submission__in=submissions),
            Q(author__user=request.user),
            Q(up_vote=True)
        ).values_list('submission_id', flat=True)

        down_votes = Vote.objects.filter(
            Q(submission__in=submissions),
            Q(author__user=request.user),
            Q(down_vote=True)
        ).values_list('submission_id', flat=True)

        up_votes_set = set(up_votes)
        down_votes_set = set(down_votes)

        for submission in submissions:
            submission.up_voted = submission.id in up_votes_set
            submission.down_voted = submission.id in down_votes_set

        '''
        for submission in submissions:
            submission.up_voted = Vote.objects.filter(submission=submission, author__user=request.user,
                                                      up_vote=True).exists()
            submission.down_voted = Vote.objects.filter(submission=submission, author__user=request.user,
                                                        down_vote=True).exists()
        '''

        paginator_submissions = Paginator(submissions, 5)
        submissions_page_number = request.GET.get('page')
        submissions_page_obj = paginator_submissions.get_page(submissions_page_number)

        most_upvoted_comment = Comment.objects.filter(submission__course=course).order_by('-score').first()

        context = {
            'course': course,
            'submissions_page_obj': submissions_page_obj,
            'course_id': course_id,
            'most_upvoted_comment': most_upvoted_comment,
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


class SearchSubmissionsView(View):
    def get(self, request, course_id):
        query = request.GET.get('title', '')
        submissions = Submission.objects.filter(Q(course_id=course_id), Q(title__icontains=query))[:5]
        submissions_json = list(submissions.values('title', 'id'))
        return JsonResponse(submissions_json, safe=False)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_has_role("student", "instructor"), name="dispatch")
class SubmitView(View):
    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)

        if not course.is_student_enrolled(request.user.profile) and request.user.profile.user_type == 'student':
            return HttpResponseForbidden("You do not have access to this course.")

        if request.user.profile.user_type == 'instructor':
            check_flag = Section.objects.filter(course=course, instructor=request.user).exists()
            if not check_flag:
                return HttpResponseForbidden("You do not have access to this course.")

        context = {
            'course_id': course_id,
        }

        return render(request, 'ciesza_submit.html', context)

    def post(self, request, course_id):
        title = request.POST.get('title')
        text = request.POST.get('text')

        course = Course.objects.get(pk=course_id)
        author = Profile.objects.get(user=request.user)

        author_name = author.nickname if author.nickname else author.user.username

        submission = Submission.objects.create(
            course=course,
            author=author,
            author_name=author_name,
            title=title,
            text=text,
        )
        submission.save()

        return redirect(reverse('SubmissionsPage', args=(course_id,)))


@method_decorator(login_required, name="dispatch")
@method_decorator(user_has_role("student", "instructor"), name="dispatch")
class CommentsView(View):
    def get(self, request, course_id, submission_id):
        course = get_object_or_404(Course, id=course_id)

        if not course.is_student_enrolled(request.user.profile) and request.user.profile.user_type == 'student':
            return HttpResponseForbidden("You do not have access to this course.")

        if request.user.profile.user_type == 'instructor':
            check_flag = Section.objects.filter(course=course, instructor=request.user).exists()
            if not check_flag:
                return HttpResponseForbidden("You do not have access to this course.")

        comments = Comment.objects.filter(submission_id=submission_id, parent_id__isnull=True).order_by('-score')
        submission = get_object_or_404(Submission, id=submission_id)

        submission.up_voted = Vote.objects.filter(submission=submission, author__user=request.user,
                                                  up_vote=True).exists()
        submission.down_voted = Vote.objects.filter(submission=submission, author__user=request.user,
                                                    down_vote=True).exists()

        for comment in comments:
            comment.set_votes(request.user)
            comment.reply_list = comment.get_replies(request.user)

        context = {
            'comments': comments,
            'submission': submission,
            'course_id': course_id,
        }

        return render(request, 'ciesza_comments.html', context)

    def post(self, request, course_id, submission_id):
        if "delete" in request.POST:                                                # for submission delete !change html
            submission = get_object_or_404(Submission, id=submission_id)
            if request.user.profile == submission.author:
                submission.text = "<p><strong>[DELETED]</strong></p>"
                submission.is_deleted = True
                submission.save()
                return redirect(reverse('CommentsPage', args=(course_id, submission_id)))
            else:
                return HttpResponseForbidden("You are not authorized to delete this submission.")

        elif "delete_comment" in request.POST:
            comment_id = request.POST.get("delete_comment")
            comment = get_object_or_404(Comment, id=comment_id)
            if request.user.profile == comment.author:
                comment.text = "<p><strong>[DELETED]</strong></p>"
                comment.is_deleted = True
                comment.save()
                return redirect(reverse('CommentsPage', args=(course_id, submission_id)))
            else:
                return HttpResponseForbidden("You are not authorized to delete this comment.")

        elif "comment" in request.POST:
            text = request.POST.get('text')
            submission = Submission.objects.get(pk=submission_id)
            author = Profile.objects.get(user=request.user)

            author_name = author.nickname if author.nickname else author.user.username

            comment = Comment.objects.create(
                submission=submission,
                author=author,
                author_name=author_name,
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

            author_name = author.nickname if author.nickname else author.user.username

            comment = Comment.objects.create(
                submission=submission,
                author=author,
                author_name=author_name,
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
        course = get_object_or_404(Course, id=course_id)

        if not course.is_student_enrolled(request.user.profile) and request.user.profile.user_type == 'student':
            return HttpResponseForbidden("You do not have access to this course.")

        if request.user.profile.user_type == 'instructor':
            check_flag = Section.objects.filter(course=course, instructor=request.user).exists()
            if not check_flag:
                return HttpResponseForbidden("You do not have access to this course.")

        author = Profile.objects.get(user_id=user_id)
        submissions = Submission.objects.filter(author=author, course_id=course_id).order_by('-score')

        for submission in submissions:
            submission.up_voted = Vote.objects.filter(submission=submission, author__user=request.user,
                                                      up_vote=True).exists()
            submission.down_voted = Vote.objects.filter(submission=submission, author__user=request.user,
                                                        down_vote=True).exists()

        current_date = timezone.now().date()
        semester = Semester.objects.filter(start_date__lte=current_date, finish_date__gte=current_date).first()

        courses = Course.objects.filter(sections__students=author).annotate(
            is_current_semester=Case(
                When(semester=semester, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        ).order_by("-is_current_semester", "course_id")



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
        course = get_object_or_404(Course, id=course_id)

        if not course.is_student_enrolled(request.user.profile) and request.user.profile.user_type == 'student':
            return HttpResponseForbidden("You do not have access to this course.")

        if request.user.profile.user_type == 'instructor':
            check_flag = Section.objects.filter(course=course, instructor=request.user).exists()
            if not check_flag:
                return HttpResponseForbidden("You do not have access to this course.")

        if user_id != request.user.pk:
            return HttpResponseForbidden("You do not have access to this profile!!")

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
                author.nickname = author_name
                author.save()

                messages.success(request, "The author name has been changed successfully!")
            else:
                messages.success(request, "The password is invalid!")

        context = {
            'author_name_form': author_name_form,
            'course_id': course_id,
            'user_id': user_id,
        }

        return render(request, 'ciesza_edit_profile.html', context)
