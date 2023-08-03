from django.core.management.base import BaseCommand
from django.core.files import File
import os

from accounts.models import Image


class Command(BaseCommand):
    help = 'Loads images from a directory into the database'

    def handle(self, *args, **options):
        directory = 'media\\images'

        for filename in os.listdir(directory):
            if filename.endswith(".jpg") or filename.endswith(".png"):
                with open(os.path.join(directory, filename), 'rb') as img_file:
                    image_model = Image()
                    image_model.image.save(filename, File(img_file))
                    image_model.save()

        self.stdout.write(self.style.SUCCESS('Images loaded successfully'))
