from worldcatclient import WorldCatClient, WorldCatSession

from conftest import (
    WORLDCAT_API_ENDPOINT,
    OCLC_AUTHENTICATION_ENDPOINT,
)

from datetime import datetime, timedelta


def test_client_instantiation(client: WorldCatClient):
    """Test instatiation of the WorldCatClient class."""

    assert isinstance(client, WorldCatClient)

    assert client.endpoint == WORLDCAT_API_ENDPOINT


def test_client_auth(client: WorldCatClient):
    """Test instatiation of the WorldCatClient class."""

    assert isinstance(client, WorldCatClient)

    assert client.endpoint == WORLDCAT_API_ENDPOINT

    assert isinstance(session := client.session, WorldCatSession)

    assert session.authendpoint == OCLC_AUTHENTICATION_ENDPOINT

    assert session.token_type is None
    assert session.access_token is None
    assert session.expires_in is None
    assert session.expires_at is None
    assert session.authenticated_scopes is None
    assert session.authenticating_institution_id is None
    assert session.context_institution_id is None

    session.authenticate()

    expires_at_actual = datetime.strptime("2026-01-02 03:04:05Z", "%Y-%m-%d %H:%M:%S%z")
    expires_at = expires_at_actual - timedelta(seconds=1)

    assert session.access_token == "<token>"
    assert session.token_type == "bearer"
    assert session.expires_in == 1234
    assert session.expires_at_actual == expires_at_actual
    assert session.expires_at == expires_at
    assert session.authenticating_institution_id == "0000"
    assert session.context_institution_id == "0000"
