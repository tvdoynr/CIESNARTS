from ckeditor.fields import RichTextField
from django.db import models
from django.utils import timezone

from accounts.models import Profile, Course


class Submission(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, related_name='submissions')
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='author_submissions')
    author_name = models.CharField(null=True)
    title = models.CharField(max_length=50)
    text = RichTextField(max_length=2000)
    score = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=timezone.now)
    comment_count = models.IntegerField(default=0)


class Comment(models.Model):
    submission = models.ForeignKey(Submission, null=True, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    author_name = models.CharField(null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE,
                               null=True,
                               blank=True,
                               related_name='replies')
    text = RichTextField(max_length=2000)
    score = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=timezone.now)


class Vote(models.Model):
    submission = models.ForeignKey(Submission, null=True, on_delete=models.CASCADE, related_name='submission_votes')
    comment = models.ForeignKey(Comment, null=True, on_delete=models.CASCADE, related_name='comment_votes')
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    up_vote = models.BooleanField(default=False)
    down_vote = models.BooleanField(default=False)
