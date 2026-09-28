from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the initial superuser Aras'

    def handle(self, *args, **options):
        if not User.objects.filter(username='Aras').exists():
            User.objects.create_superuser(
                username='Aras',
                email='aras@dicoding.com',
                password='1234qwer!@#$'
            )
            self.stdout.write(self.style.SUCCESS("Superuser 'Aras' created successfully."))
        else:
            u = User.objects.get(username='Aras')
            u.set_password('1234qwer!@#$')
            u.is_superuser = True
            u.is_staff = True
            u.save()
            self.stdout.write(self.style.SUCCESS("Superuser 'Aras' updated successfully."))
