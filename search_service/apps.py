from django.apps import AppConfig


class SearchServiceConfig(AppConfig):
    name = "search_service"

    def ready(self):
        from .signals import (
            index_json_resource,
        )
