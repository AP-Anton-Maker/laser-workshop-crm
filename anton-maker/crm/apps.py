# CRM Application Configuration

from django.apps import AppConfig


class CrmConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crm'
    verbose_name = 'Управление производством'
    
    def ready(self):
        # Import signals here if needed
        pass
