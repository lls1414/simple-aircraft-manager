"""Per-aircraft feature flag helpers."""
from django.conf import settings

# Builtin feature definitions. Each entry is a dict with:
#   name        — slug used in DB / API
#   label       — human-readable display name
#   description — one-line description shown in the Settings tab
#
# Plugins may register additional features via SAMPluginConfig.aircraft_features.
# CoreConfig.ready() registers these builtins through the same registry path.
BUILTIN_FEATURE_CATALOG = [
    {
        'name': 'flight_tracking',
        'label': 'Flight Tracking',
        'description': 'Flight log tab and Log Flight button',
    },
    {
        'name': 'oil_consumption',
        'label': 'Oil Consumption',
        'description': 'Oil usage records and consumption chart',
    },
    {
        'name': 'fuel_consumption',
        'label': 'Fuel Consumption',
        'description': 'Fuel usage records and burn rate chart',
    },
    {
        'name': 'oil_analysis',
        'label': 'Oil Analysis',
        'description': 'Oil analysis lab report tracking',
    },
    {
        'name': 'airworthiness_enforcement',
        'label': 'Airworthiness Enforcement',
        'description': 'Block flight logging and hour updates when aircraft is grounded',
    },
    {
        'name': 'sharing',
        'label': 'Public Sharing',
        'description': 'Share links and public access',
    },
]


def get_feature_catalog():
    """Return the full feature catalog (builtin + plugin) as a list of dicts.

    Each dict has 'name', 'label', and 'description' keys.
    Builtins are always first; plugin features follow in registration order.
    """
    from core.plugins import registry
    return registry.feature_catalog


def get_known_feature_names():
    """Return a list of all known feature name slugs (builtin + plugin)."""
    return [f['name'] for f in get_feature_catalog()]


def feature_available(feature_name: str, aircraft=None) -> bool:
    """
    Return True if the named feature is available for the given aircraft.

    Resolution order:
    1. Global DISABLED_FEATURES setting  — False if listed
    2. Per-aircraft AircraftFeature row  — use enabled field if row exists
    3. Default                           — True (all features on by default)
    """
    # 1. Global kill switch
    if feature_name in getattr(settings, 'DISABLED_FEATURES', []):
        return False
    # 2. Per-aircraft override
    if aircraft is not None:
        from core.models import AircraftFeature
        try:
            flag = AircraftFeature.objects.get(aircraft=aircraft, feature=feature_name)
            return flag.enabled
        except AircraftFeature.DoesNotExist:
            pass
    # 3. Default — enabled
    return True
