from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Register built-in feature flags through the same registry path that
        # plugins use, so builtins and plugin features are treated identically.
        from core.features import BUILTIN_FEATURE_CATALOG
        from core.plugins import registry
        registry.register_features(BUILTIN_FEATURE_CATALOG)
