# Generated by Django 4.2.2 on 2023-07-12 07:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_transcript_grade'),
        ('ciesza', '0002_comment_submission'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='course',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.course'),
        ),
    ]
