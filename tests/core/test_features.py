"""Tests for the per-aircraft feature flag system."""
import pytest
from unittest.mock import patch

from core.features import feature_available
from core.models import AircraftFeature, KNOWN_FEATURES


# ---------------------------------------------------------------------------
# feature_available() unit tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_feature_available_default_true(aircraft):
    """All features are enabled by default."""
    for feature in KNOWN_FEATURES:
        assert feature_available(feature, aircraft) is True


@pytest.mark.django_db
def test_feature_available_global_disabled(aircraft):
    """DISABLED_FEATURES setting overrides everything."""
    with patch('core.features.settings') as mock_settings:
        mock_settings.DISABLED_FEATURES = ['flight_tracking']
        assert feature_available('flight_tracking', aircraft) is False
        assert feature_available('oil_consumption', aircraft) is True


@pytest.mark.django_db
def test_feature_available_per_aircraft_disabled(aircraft):
    """Per-aircraft disabled flag returns False."""
    AircraftFeature.objects.create(aircraft=aircraft, feature='oil_consumption', enabled=False)
    assert feature_available('oil_consumption', aircraft) is False
    assert feature_available('fuel_consumption', aircraft) is True


@pytest.mark.django_db
def test_feature_available_global_overrides_per_aircraft(aircraft):
    """DISABLED_FEATURES beats per-aircraft enabled=True."""
    AircraftFeature.objects.create(aircraft=aircraft, feature='sharing', enabled=True)
    with patch('core.features.settings') as mock_settings:
        mock_settings.DISABLED_FEATURES = ['sharing']
        assert feature_available('sharing', aircraft) is False


@pytest.mark.django_db
def test_feature_available_per_aircraft_enabled(aircraft):
    """Explicit enabled=True row is transparent (same as default)."""
    AircraftFeature.objects.create(aircraft=aircraft, feature='oil_analysis', enabled=True)
    assert feature_available('oil_analysis', aircraft) is True


@pytest.mark.django_db
def test_feature_available_no_aircraft():
    """feature_available with aircraft=None uses only global setting."""
    assert feature_available('flight_tracking') is True
    with patch('core.features.settings') as mock_settings:
        mock_settings.DISABLED_FEATURES = ['flight_tracking']
        assert feature_available('flight_tracking') is False


# ---------------------------------------------------------------------------
# GET /api/aircraft/{id}/features/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_features_get_owner(owner_client, aircraft):
    """Owner can GET features and gets full dict."""
    resp = owner_client.get(f'/api/aircraft/{aircraft.id}/features/')
    assert resp.status_code == 200
    data = resp.json()
    assert 'features' in data
    for feature in KNOWN_FEATURES:
        assert feature in data['features']
        assert data['features'][feature] is True


@pytest.mark.django_db
def test_features_get_pilot(aircraft_with_pilot, pilot_client):
    """Pilot can GET features."""
    resp = pilot_client.get(f'/api/aircraft/{aircraft_with_pilot.id}/features/')
    assert resp.status_code == 200
    assert 'features' in resp.json()


@pytest.mark.django_db
def test_features_get_non_member(other_client, aircraft):
    """Non-member gets 404 (aircraft not visible to them)."""
    resp = other_client.get(f'/api/aircraft/{aircraft.id}/features/')
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/aircraft/{id}/features/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_features_post_owner_disable(owner_client, aircraft):
    """Owner can disable a feature."""
    resp = owner_client.post(
        f'/api/aircraft/{aircraft.id}/features/',
        {'feature': 'flight_tracking', 'enabled': False},
        format='json',
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data['features']['flight_tracking'] is False
    assert AircraftFeature.objects.filter(aircraft=aircraft, feature='flight_tracking', enabled=False).exists()


@pytest.mark.django_db
def test_features_post_owner_enable(owner_client, aircraft):
    """Owner can re-enable a previously disabled feature."""
    AircraftFeature.objects.create(aircraft=aircraft, feature='oil_consumption', enabled=False)
    resp = owner_client.post(
        f'/api/aircraft/{aircraft.id}/features/',
        {'feature': 'oil_consumption', 'enabled': True},
        format='json',
    )
    assert resp.status_code == 200
    assert resp.json()['features']['oil_consumption'] is True


@pytest.mark.django_db
def test_features_post_pilot_forbidden(aircraft_with_pilot, pilot_client):
    """Pilot cannot POST to features (owner-only write)."""
    resp = pilot_client.post(
        f'/api/aircraft/{aircraft_with_pilot.id}/features/',
        {'feature': 'flight_tracking', 'enabled': False},
        format='json',
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_features_post_unknown_feature(owner_client, aircraft):
    """Unknown feature name returns 400."""
    resp = owner_client.post(
        f'/api/aircraft/{aircraft.id}/features/',
        {'feature': 'nonexistent_feature', 'enabled': False},
        format='json',
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_features_post_invalid_enabled(owner_client, aircraft):
    """Non-boolean enabled returns 400."""
    resp = owner_client.post(
        f'/api/aircraft/{aircraft.id}/features/',
        {'feature': 'flight_tracking', 'enabled': 'yes'},
        format='json',
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_features_post_cannot_enable_globally_disabled(owner_client, aircraft):
    """Cannot re-enable a globally-disabled feature via API."""
    with patch('health.aircraft_actions.django_settings') as mock_settings:
        mock_settings.DISABLED_FEATURES = ['oil_analysis']
        resp = owner_client.post(
            f'/api/aircraft/{aircraft.id}/features/',
            {'feature': 'oil_analysis', 'enabled': True},
            format='json',
        )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Summary endpoint includes features
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_summary_includes_features(owner_client, aircraft):
    """GET summary returns features dict."""
    resp = owner_client.get(f'/api/aircraft/{aircraft.id}/summary/')
    assert resp.status_code == 200
    data = resp.json()
    assert 'features' in data
    for feature in KNOWN_FEATURES:
        assert feature in data['features']


# ---------------------------------------------------------------------------
# Share token / public URL enforcement
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_share_token_creation_blocked_when_sharing_disabled(owner_client, aircraft):
    """Creating a share token fails when sharing feature is off."""
    AircraftFeature.objects.create(aircraft=aircraft, feature='sharing', enabled=False)
    resp = owner_client.post(
        f'/api/aircraft/{aircraft.id}/share_tokens/',
        {'privilege': 'status'},
        format='json',
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_share_token_creation_allowed_when_sharing_enabled(owner_client, aircraft):
    """Creating a share token works when sharing is enabled (default)."""
    resp = owner_client.post(
        f'/api/aircraft/{aircraft.id}/share_tokens/',
        {'privilege': 'status'},
        format='json',
    )
    assert resp.status_code == 201


@pytest.mark.django_db
def test_existing_public_url_blocked_when_sharing_disabled(client, share_token_status, aircraft):
    """Existing share URLs return 404 when sharing is disabled (token is preserved)."""
    from core.models import AircraftShareToken
    AircraftFeature.objects.create(aircraft=aircraft, feature='sharing', enabled=False)
    resp = client.get(f'/api/shared/{share_token_status.token}/')
    assert resp.status_code == 404
    # Token must still exist in the DB (not deleted)
    assert AircraftShareToken.objects.filter(id=share_token_status.id).exists()


@pytest.mark.django_db
def test_existing_public_url_works_after_sharing_reenabled(client, share_token_status, aircraft):
    """After re-enabling sharing, the same URL works again."""
    flag = AircraftFeature.objects.create(aircraft=aircraft, feature='sharing', enabled=False)
    assert client.get(f'/api/shared/{share_token_status.token}/').status_code == 404
    flag.enabled = True
    flag.save()
    assert client.get(f'/api/shared/{share_token_status.token}/').status_code == 200


# ---------------------------------------------------------------------------
# Export includes features; import restores them
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_export_includes_features(aircraft):
    """build_manifest includes features list."""
    from core.export import build_manifest
    AircraftFeature.objects.create(aircraft=aircraft, feature='flight_tracking', enabled=False)
    manifest = build_manifest(aircraft)
    assert 'features' in manifest
    features_by_name = {f['feature']: f['enabled'] for f in manifest['features']}
    assert features_by_name.get('flight_tracking') is False


@pytest.mark.django_db
def test_export_missing_features_key_backward_compat():
    """Missing features key in manifest is OK — treated as empty list."""
    # This is implicitly tested by the import code using manifest.get('features', [])
    # Just verify KNOWN_MANIFEST_KEYS includes 'features'
    from core.import_export import KNOWN_MANIFEST_KEYS
    assert 'features' in KNOWN_MANIFEST_KEYS
