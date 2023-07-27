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

    def semester_length(self):
        return (self.finish_date - self.start_date).days

    def elapsed_days(self):
        return (timezone.now().date() - self.start_date).days

    def __str__(self):
        return self.name


class Course(models.Model):
    course_id = models.CharField(max_length=10)
    course_name = models.CharField(max_length=100)
    description = models.TextField()
    course_credit = models.IntegerField()
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, null=True)
    is_active = models.BooleanField(default=False)

    def is_student_enrolled(self, student):
        return self.sections.filter(students=student).exists()

    def can_be_created(self):
        return self.semester.has_started()

    def __str__(self):
        return self.course_id

    def save(self, *args, **kwargs):
        creating_new_course = self.pk is None
        super(Course, self).save(*args, **kwargs)

        if creating_new_course:
            for i in range(1, 4):
                section = Section(course=self, NumberOfStudents=0, Classroom="")
                section.save()


class Section(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    NumberOfStudents = models.IntegerField()
    Classroom = models.CharField(max_length=100)
    Instructor = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    students = models.ManyToManyField(Profile, related_name='enrolled_sections')

    def can_be_added(self):
        return self.NumberOfStudents < 40

    def __str__(self):
        section_id = self.id % 3
        if section_id == 0:
            section_id += 3
        return f'{self.course.course_id} Section {section_id}'


class Transcript(models.Model):
    student = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.student.user.first_name} {self.student.user.last_name} Transcript'


class Grade(models.Model):
    transcript = models.ForeignKey(Transcript, on_delete=models.CASCADE, related_name='grades')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.FloatField()

    def __str__(self):
        return f'Grade for {self.transcript.student.user.first_name} {self.transcript.student.user.last_name} ' \
               f'in {self.course.course_id} by {self.instructor.first_name} {self.instructor.last_name}'

