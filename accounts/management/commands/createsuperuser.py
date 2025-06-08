from django.contrib.auth.management.commands import createsuperuser
from django.core.management import CommandError
from django.contrib.auth import get_user_model

class Command(createsuperuser.Command):
    def handle(self, *args, **options):
        UserModel = get_user_model()

        try:
            # Get username and email using parent class method
            credentials = super().handle(*args, **options)

            # Get phone number
            while True:
                phone_number = input('Phone Number: ')
                if phone_number:
                    try:
                        if UserModel.objects.filter(phone_number=phone_number).exists():
                            self.stderr.write("Error: That phone number is already taken.")
                            continue
                        break
                    except Exception as e:
                        self.stderr.write(f"Error: {str(e)}")
                        continue
                else:
                    self.stderr.write("Error: Phone number is required")

            # Get address
            while True:
                address = input('Address: ')
                if address:
                    break
                self.stderr.write("Error: Address is required")

            # Update the user with phone number and address
            if isinstance(credentials, dict):
                user = UserModel.objects.get(username=credentials['username'])
            else:
                user = credentials
            user.phone_number = phone_number
            user.address = address
            user.save()

            return user

        except Exception as e:
            raise CommandError(str(e))
