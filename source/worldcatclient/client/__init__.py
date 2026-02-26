from worldcatclient.logging import logger
from worldcatclient.enumerations import (
    WorldCatScope,
    WorldCatOrderingSearchAPI,
)
from worldcatclient.exceptions import WorldCatClientError
from worldcatclient.records import WorldCatRecord
from worldcatclient.session import WorldCatSession
from worldcatclient.constants import (
    WORLDCAT_API_ENDPOINT,
    OCLC_AUTHENTICATION_ENDPOINT,
)

from collections.abc import Iterator

import requests

logger = logger.getChild(__name__)


class WorldCatClient(object):
    """The WorldCatClient supports interacting with the WorldCat API."""

    _endpoint: str = None
    _client_id: str = None
    _secret: str = None
    _scopes: list[WorldCatScope] = None
    _session: WorldCatSession = None
    _timeout: int = None

    def __init__(
        self,
        client_id: str,
        secret: str,
        endpoint: str = None,
        authendpoint: str = None,
        scopes: list[WorldCatScope] | list[str] = None,
        timeout: int = 10,
    ):
        """Supports initialising the WorldCatClient class."""

        if not isinstance(client_id, str):
            raise TypeError("The 'client_id' argument must have a string value!")

        self._client_id: str = client_id

        if not isinstance(secret, str):
            raise TypeError("The 'secret' argument must have a string value!")

        self._secret: str = secret

        if endpoint is None:
            endpoint: str = WORLDCAT_API_ENDPOINT
        elif not isinstance(endpoint, str):
            raise TypeError("The 'endpoint' argument must have a string value!")
        elif not (endpoint.startswith("http://") or endpoint.startswith("https://")):
            raise ValueError(
                "The 'endpoint' argument must have a valid HTTP URL value!"
            )

        self._endpoint: str = endpoint.strip("/")

        if authendpoint is None:
            authendpoint: str = OCLC_AUTHENTICATION_ENDPOINT
        elif not isinstance(authendpoint, str):
            raise TypeError("The 'authendpoint' argument must have a string value!")
        elif not (
            authendpoint.startswith("http://") or authendpoint.startswith("https://")
        ):
            raise ValueError(
                "The 'authendpoint' argument must have a valid HTTP URL value!"
            )

        self._authendpoint: str = authendpoint.strip("/")

        self._scopes: list[WorldCatScope] = []

        if scopes is None:
            self._scopes.append(WorldCatScope.SearchAPI)
        elif not isinstance(scopes, list):
            raise TypeError(
                "The 'scopes' argument, if specified, must reference a list value!"
            )
        else:
            for scope in scopes:
                if isinstance(scope, WorldCatScope):
                    self._scopes.append(scope)
                elif isinstance(scope, str):
                    if (reconciled := WorldCatScope.reconcile(scope)) is None:
                        raise ValueError(
                            "Scopes expressed as strings must match a valid scope option!"
                        )
                    elif isinstance(scope, WorldCatScope):
                        self._scopes.append(reconciled)

        if not isinstance(timeout, int):
            raise TypeError("The 'timeout' argument must have an integer value!")
        elif not 0 < timeout < 120:
            raise ValueError(
                "The 'timeout' argument must have an integer value between 1-120 seconds!"
            )
        else:
            self._timeout = timeout

    @property
    def endpoint(self) -> str:
        return self._endpoint

    @property
    def scopes(self) -> list[WorldCatScope]:
        return self._scopes

    @property
    def timeout(self) -> int:
        return self._timeout

    @property
    def session(self) -> WorldCatSession:
        """Supports initialising and returning the WorldCatSession."""

        if self._session is None:
            self._session = WorldCatSession(
                endpoint=self._endpoint,
                client_id=self._client_id,
                secret=self._secret,
                scopes=self._scopes,
                authendpoint=self._authendpoint,
            )

        return self._session

    def search(
        self,
        query: str,
        limit: int = 10,
        offset: int = None,
        timeout: int = None,
        order: WorldCatOrderingSearchAPI = WorldCatOrderingSearchAPI.BestMatch,
        parsed: bool = False,
        **kwargs,
    ) -> Iterator[dict[str, object]] | Iterator[WorldCatRecord]:
        """Supports interacting with the WorldCat Search API endpoint."""

        if not self.session.scoped(WorldCatScope.SearchAPI):
            raise WorldCatClientError(
                "The WorldCatClient.search() method cannot be used without the WorldCat Search API scope!"
            )

        if not isinstance(query, str):
            raise TypeError("The 'query' argument must have a string value!")
        elif not len(query := query.strip()) > 0:
            raise ValueError(
                "The 'query' argument must have an non-empty string value!"
            )

        if not isinstance(limit, int):
            raise TypeError("The 'limit' argument must have an integer value!")
        elif not 0 < limit <= 50:
            raise ValueError(
                "The 'limit' argument must have an integer value between 1-50!"
            )

        if offset is None:
            pass
        elif not isinstance(offset, int):
            raise TypeError("The 'offset' argument must have an integer value!")
        elif not 0 <= offset:
            raise ValueError(
                "The 'offset' argument must have a positive integer value!"
            )

        if timeout is None:
            timeout = self.timeout
        elif not isinstance(timeout, int):
            raise TypeError("The 'timeout' argument must have an integer value!")
        elif not 0 < timeout <= 120:
            raise ValueError(
                "The 'timeout' argument must have an integer value between 1-120!"
            )

        if not isinstance(order, WorldCatOrderingSearchAPI):
            raise TypeError(
                "The 'order' argument must reference a WorldCatOrderingSearchAPI ennumeration option!"
            )

        if not isinstance(parsed, bool):
            raise TypeError("The 'parsed' argument must have a boolean value!")

        url: str = self._endpoint + "/worldcat/search/v2/brief-bibs"

        logger.debug(
            "%s.search(query: %s, limit: %d, offset: %d) URL => %s",
            self.__class__.__name__,
            query,
            limit,
            offset,
            url,
        )

        headers = {"Accept": "application/json"}

        params = {"q": query, "limit": limit, "orderBy": order.value}

        for key, value in kwargs.items():
            params[key] = value

        if offset is None:
            offset = 1
        else:
            params["offset"] = offset

        response: requests.Response = None

        try:
            response = self.session.get(
                url=url,
                headers=headers,
                params=params,
                timeout=timeout,
            )

            response.raise_for_status()

            if response.status_code == 200:
                if isinstance(data := response.json(), dict):
                    if isinstance(count := data.get("numberOfRecords"), int):
                        if isinstance(records := data.get("briefRecords"), list):
                            for index, data in enumerate(records, start=offset):
                                if parsed is True:
                                    yield WorldCatRecord(data=data)
                                else:
                                    yield data

                            if (index < count) and ((offset + limit) < count):
                                yield from self.search(
                                    query=query,
                                    limit=limit,
                                    offset=(offset + limit),
                                    timeout=timeout,
                                    parsed=parsed,
                                )

        except requests.exceptions.RequestException as exception:
            logger.error(f"An error occurred during the search request: {exception}")
            logger.debug(response.status_code)
            logger.debug(response.headers)
            logger.debug(response.content)


__all__ = [
    "WorldCatClient",
]
