from django.apps import AppConfig


class ExemplarConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'exemplar'

    def ready(self): 
        from .signals import (
                index_exemplar_resource, 
                )
