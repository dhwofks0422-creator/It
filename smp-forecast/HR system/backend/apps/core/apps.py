from django.apps import AppConfig
from django.db.models.signals import post_migrate

def ensure_default_admin(sender, **kwargs):
    try:
        from apps.core.models import User
        admin_user, created = User.objects.get_or_create(
            employee_id='ADMIN',
            defaults={
                'name': '최고관리자',
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin1234!')
            admin_user.save()
    except Exception:
        pass

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = '인사평가 코어 시스템'

    def ready(self):
        post_migrate.connect(ensure_default_admin, sender=self)


