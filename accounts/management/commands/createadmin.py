from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates a superuser account'

    def handle(self, *args, **options):
        username = input('Username: ').strip()
        if not username:
            self.stderr.write('Error: Username is required')
            return

        email = input('Email: ').strip()
        if not email or '@' not in email:
            self.stderr.write('Error: Valid email is required')
            return

        password = input('Password: ').strip()
        if not password:
            self.stderr.write('Error: Password is required')
            return

        phone = input('Phone number: ').strip()
        if not phone:
            self.stderr.write('Error: Phone number is required')
            return

        address = input('Address: ').strip()
        if not address:
            self.stderr.write('Error: Address is required')
            return

        try:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                phone_number=phone,
                address=address
            )
            self.stdout.write(self.style.SUCCESS('Superuser created successfully'))
        except Exception as e:
            self.stderr.write(f'Error: {str(e)}')User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            phone_number=phone_number,
            address=address
        )
        self.stdout.write(self.style.SUCCESS('Superuser created successfully.'))
