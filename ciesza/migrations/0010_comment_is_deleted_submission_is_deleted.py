# Generated by Django 4.2.2 on 2023-08-03 20:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ciesza', '0009_alter_comment_author'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='submission',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]
