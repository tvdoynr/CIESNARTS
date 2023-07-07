# Generated by Django 4.2.2 on 2023-07-06 11:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0007_remove_profile_sections_section_students'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='section',
            name='Instructors',
        ),
        migrations.AddField(
            model_name='section',
            name='Instructor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
