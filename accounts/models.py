from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Image(models.Model):
    image = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('manager', 'Manager'),
    )
    nickname = models.CharField(max_length=30, blank=True, null=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')
    profile_picture = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, default=6)


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
            sections_list = [Section(course=self, NumberOfStudents=0, Classroom="") for _ in range(3)]
            Section.objects.bulk_create(sections_list)
            '''
            for i in range(1, 4):
                section = Section(course=self, NumberOfStudents=0, Classroom="")
                section.save()
            '''

class Section(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    number_of_students = models.IntegerField()
    classroom = models.CharField(max_length=100)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    students = models.ManyToManyField(Profile, related_name='enrolled_sections')

    def can_be_added(self):
        return self.number_of_students < 40

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

