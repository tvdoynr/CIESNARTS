# Generated by Django 4.2.2 on 2023-07-19 13:10

import ckeditor.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ciesza', '0007_vote'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='text',
            field=ckeditor.fields.RichTextField(max_length=2000),
        ),
        migrations.AlterField(
            model_name='submission',
            name='text',
            field=ckeditor.fields.RichTextField(max_length=2000),
        ),
    ]
