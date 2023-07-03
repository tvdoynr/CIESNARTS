from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('manager', 'Manager'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')


class Semester(models.Model):
    name = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    finish_date = models.DateField()

    def has_started(self):
        current_date = timezone.now().date()
        return self.start_date <= current_date <= self.finish_date

    def __str__(self):
        return self.name


class Course(models.Model):
    CourseID = models.CharField(max_length=10, unique=True)
    CourseName = models.CharField(max_length=100)
    Description = models.TextField()
    CourseCredit = models.IntegerField()
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, null=True)

    def can_be_created(self):
        return self.semester.has_started()

    def __str__(self):
        return self.CourseID


class Section(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    NumberOfStudents = models.IntegerField()
    Classroom = models.CharField(max_length=100)
    Instructors = models.ManyToManyField(User)

    def can_be_added(self):
        return self.NumberOfStudents < 40

    def __str__(self):
        return f'{self.course.CourseID} Section {self.id}'
