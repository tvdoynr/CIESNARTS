# Generated by Django 4.2.2 on 2023-07-06 08:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_profile_sections'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='sections',
        ),
        migrations.AddField(
            model_name='section',
            name='students',
            field=models.ManyToManyField(related_name='enrolled_sections', to='accounts.profile'),
        ),
    ]
