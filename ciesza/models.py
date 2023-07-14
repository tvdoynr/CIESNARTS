from django.db import models
from django.utils import timezone

from accounts.models import Profile, Course


class Submission(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, related_name='submissions')
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='author_submissions')
    author_name = models.CharField(null=True)
    title = models.CharField(max_length=50)
    text = models.TextField(max_length=2000)
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
    text = models.TextField(max_length=2000)
    score = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=timezone.now)
