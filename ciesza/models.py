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
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='author_comments')
    author_name = models.CharField(null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE,
                               null=True,
                               blank=True,
                               related_name='replies')
    text = RichTextField(max_length=2000)
    score = models.IntegerField(default=0)
    timestamp = models.DateTimeField(default=timezone.now)

    def set_votes(self, user):
        self.up_voted = Vote.objects.filter(comment=self, author__user=user, up_vote=True).exists()
        self.down_voted = Vote.objects.filter(comment=self, author__user=user, down_vote=True).exists()

    def get_replies(self, user):
        replies = Comment.objects.filter(parent=self).order_by('-score')
        for reply in replies:
            reply.set_votes(user)
            reply.reply_list = reply.get_replies(user)
        return replies


class Vote(models.Model):
    submission = models.ForeignKey(Submission, null=True, on_delete=models.CASCADE, related_name='submission_votes')
    comment = models.ForeignKey(Comment, null=True, on_delete=models.CASCADE, related_name='comment_votes')
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    up_vote = models.BooleanField(default=False)
    down_vote = models.BooleanField(default=False)
