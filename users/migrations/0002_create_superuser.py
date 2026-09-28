from django.db import migrations


def create_initial_superuser(apps, schema_editor):
    User = apps.get_model('users', 'CustomUser')
    if not User.objects.filter(username='Aras').exists():
        user = User(
            username='Aras',
            email='aras@dicoding.com',
            is_staff=True,
            is_superuser=True,
        )
        # We need to set hashed password
        from django.contrib.auth.hashers import make_password
        user.password = make_password('1234qwer!@#$')
        user.save()


def remove_initial_superuser(apps, schema_editor):
    User = apps.get_model('users', 'CustomUser')
    User.objects.filter(username='Aras').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_superuser, remove_initial_superuser),
    ]
