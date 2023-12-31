# Generated by Django 4.2.2 on 2023-06-22 12:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('CourseID', models.CharField(max_length=10, unique=True)),
                ('CourseName', models.CharField(max_length=100)),
                ('Description', models.TextField()),
                ('CourseCredit', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Section',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('NumberOfStudents', models.IntegerField()),
                ('Classroom', models.CharField(max_length=100)),
                ('Instructors', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='accounts.course')),
            ],
        ),
    ]
