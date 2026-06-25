import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Membuat superuser dari environment variable DJANGO_SUPERUSER_USERNAME/"
        "PASSWORD/EMAIL jika belum ada. Aman dijalankan berulang kali (idempotent),"
        " jadi cocok dipanggil otomatis setiap deploy."
    )

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')

        if not username or not password:
            self.stdout.write('DJANGO_SUPERUSER_USERNAME/PASSWORD tidak di-set, dilewati.')
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(f'Superuser "{username}" sudah ada, dilewati.')
            return

        User.objects.create_superuser(username=username, password=password, email=email)
        self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" berhasil dibuat.'))
