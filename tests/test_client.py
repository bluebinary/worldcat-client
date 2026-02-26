from worldcatclient import WorldCatClient, WorldCatRecord

from conftest import (
    WORLDCAT_API_ENDPOINT,
)


def test_client_instantiation(client: WorldCatClient):
    """Test instatiation of the WorldCatClient class."""

    assert isinstance(client, WorldCatClient)

    assert client.endpoint == WORLDCAT_API_ENDPOINT


def test_client_search(client: WorldCatClient):
    """Test searching via the WorldCatClient class."""

    assert isinstance(client, WorldCatClient)

    assert client.endpoint == WORLDCAT_API_ENDPOINT

    isbn: str = "0-9613921-1-8"

    query: str = f"bn:{isbn}"

    for index, record in enumerate(client.search(query=query, parsed=True), start=1):
        assert isinstance(record, WorldCatRecord)
