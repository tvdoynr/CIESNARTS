# Generated by Django 4.2.2 on 2023-07-06 08:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_course_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='sections',
            field=models.ManyToManyField(related_name='students', to='accounts.section'),
        ),
    ]
