"""Per-aircraft feature flag helpers."""
from django.conf import settings


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
