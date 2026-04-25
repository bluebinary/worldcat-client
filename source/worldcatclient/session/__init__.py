from __future__ import annotations

from worldcatclient.logging import logger

from worldcatclient.enumerations import WorldCatScope

from worldcatclient.exceptions import (
    WorldCatAuthenticationError,
    WorldCatRequestError,
)

from worldcatclient.constants import (
    DEFAULT_TIMEOUTS,
    OCLC_AUTHENTICATION_ENDPOINT,
)

from worldcatclient.utilities import (
    get_exception_locations,
)

from datetime import datetime, timezone, timedelta

import requests
import json

from urllib3.util import Retry

logger = logger.getChild(__name__)


class WorldCatSession(requests.Session):
    """The WorldCatSession class creates a reusable session with authentication."""

    _methods: list[str] = [
        "HEAD",
        "GET",
        "PUT",
        "PATCH",
        "POST",
        "DELETE",
        "OPTIONS",
        "TRACE",
    ]

    _endpoint: str = None
    _client_id: str = None
    _secret: str = None
    _scopes: list[WorldCatScope] | list[str] = None
    _authendpoint: str = None
    _retries: int = None

    _authenticated: bool = False
    _access_token: str = None
    _expires_at: datetime = None
    _authenticating_institution_id: str = None
    _context_institution_id: str = None
    _authenticated_scopes: list[str] = None
    _token_type: str = None
    _expires_in: int = None
    _principal_id: str = None
    _principal_idns: str = None

    def __init__(
        self,
        *args,
        endpoint: str,
        client_id: str,
        secret: str,
        authendpoint: str = None,
        scopes: list[WorldCatScope] | list[str] = None,
        retries: int = 3,
        retry_statuses: tuple[int] | list[int] | set[int] = (
            408,
            429,
            500,
            502,
            503,
            504,
            522,
        ),
        backoff_factor: float | int = 1.0,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        if not isinstance(endpoint, str):
            raise TypeError("The 'endpoint' argument must have a string value!")

        self._endpoint: str = endpoint.strip("/")

        if not isinstance(client_id, str):
            raise TypeError("The 'client_id' argument must have a string value!")

        self._client_id: str = client_id

        if not isinstance(secret, str):
            raise TypeError("The 'secret' argument must have a string value!")

        self._secret: str = secret

        if authendpoint is None:
            self._authendpoint: str = OCLC_AUTHENTICATION_ENDPOINT
        elif isinstance(authendpoint, str):
            self._authendpoint: str = authendpoint.strip("/")
        else:
            raise TypeError(
                "The 'authendpoint' argument, if specified, must have a string value!"
            )

        self._scopes: list[str] = []

        if scopes is None:
            pass
        elif not isinstance(scopes, list):
            raise TypeError("The 'scopes' argument must reference a list value!")
        else:
            for scope in scopes:
                if isinstance(scope, WorldCatScope):
                    self._scopes.append(scope)
                elif isinstance(scope, str):
                    if reconciled := WorldCatScope.reconcile(scope):
                        self._scopes.append(reconciled)
                    elif ":" in scope:
                        self._scopes.append(scope)
                    else:
                        raise TypeError(f"An invalid scope, '{scope}', was specified!")
                else:
                    raise TypeError(
                        "Each value in the 'scopes' list must be a WorldCatScope enumeration option or a scope mnemonic string!"
                    )

        if retries is None:
            pass
        elif not isinstance(retries, int):
            raise TypeError("The 'retries' argument must have an integer value!")
        elif not 0 <= retries <= 10:
            raise ValueError(
                "The 'retries' argument must have a positive integer value between 0–10!"
            )

        self._retries: int = retries

        if isinstance(retry_statuses, (tuple, list, set)):
            retry_statuses = list(retry_statuses)

            for retry_status in retry_statuses:
                if not isinstance(retry_status, int):
                    raise TypeError(
                        "Each entry in the 'retry_statuses' argument must have an integer value!"
                    )
                elif not 400 <= retry_status <= 599:
                    raise ValueError(
                        "Each entry in the 'retry_statuses' argument must have an integer value between 400-599!"
                    )
        else:
            raise TypeError(
                "The 'retry_statuses' argument must have a tuple, list or set value of integers!"
            )

        if isinstance(backoff_factor, (float, int)):
            backoff_factor = float(backoff_factor)

            if not 0.1 <= backoff_factor <= 10.0:
                raise ValueError(
                    "The 'backoff_factor' argument must have a value between 0.1 – 10.0!"
                )
        else:
            raise TypeError(
                "The 'backoff_factor' argument must have a float or integer value!"
            )

        # Create and configure a HTTP adapter with the configured retry strategy
        adapter = requests.adapters.HTTPAdapter(
            max_retries=Retry(
                total=retries,  # Total number of retries per request
                status_forcelist=retry_statuses,  # Statuses to retry
                backoff_factor=backoff_factor,  # Exponential backoff (e.g., 0s, 2s, 4s...)
                allowed_methods=["HEAD", "GET"],  # Methods to retry requests for
            ),
        )

        # Mount the adapters into the current session
        self.mount("http://", adapter)
        self.mount("https://", adapter)

    def __del__(self):
        logger.debug("%s.__del__()", self.__class__.__name__)

    def __str__(self) -> str:
        if self._session_id is None:
            return "<%s(inactive)>" % (self.__class__.__name__)
        else:
            return "<%s(id: %s, token: %s)>" % (
                self.__class__.__name__,
                self.headers.get("X-SESSION-ID"),
                self.cookies.get("X-TOKEN"),
            )

    @property
    def endpoint(self) -> str:
        """Returns the configured service endpoint."""

        return self._endpoint

    @property
    def authendpoint(self) -> str:
        """Returns the configured authentication endpoint."""

        return self._authendpoint

    @property
    def scopes(self) -> list[WorldCatScope] | list[str]:
        """Returns the configured scopes."""

        return self._scopes

    @property
    def retries(self) -> int:
        """Returns the configured maximum retry count."""

        return self._retries

    @property
    def active(self) -> bool:
        """Determines if the session should be considered active or not."""

        return self._authenticated is True

    @property
    def access_token(self) -> str | None:
        """Returns the requested authentication access token."""

        return self._access_token

    @property
    def expires_at(self) -> datetime | None:
        """Returns the authentication access token expiry date (minus a second)."""

        if isinstance(self._expires_at, datetime):
            # Minus a second from the expiry date to account for any auth check delays
            return self._expires_at - timedelta(seconds=1)

    @property
    def expires_at_actual(self) -> datetime | None:
        """Returns the authentication access token expiry date."""

        if isinstance(self._expires_at, datetime):
            return self._expires_at

    @property
    def authenticating_institution_id(self) -> str | None:
        """Returns the authenticating institution identifier."""

        return self._authenticating_institution_id

    @property
    def context_institution_id(self) -> str | None:
        """Returns the context institution identifier."""

        return self._context_institution_id

    @property
    def authenticated_scopes(self) -> list[str]:
        """Returns the authenticated scopes."""

        return self._authenticated_scopes

    @property
    def token_type(self) -> str | None:
        """Returns the authenticated token type."""

        return self._token_type

    @property
    def expires_in(self) -> int | None:
        """Returns the authenticated token expiry counter."""

        return self._expires_in

    @property
    def principal_id(self) -> str | None:
        """Returns the authenticated session's associated principal identifier."""

        return self._principal_id

    @property
    def principal_idns(self) -> str | None:
        """Returns the authenticated session's associated principal IDNS."""

        return self._principal_idns

    @property
    def expired(self) -> bool:
        """Supports determining if the session token has expired or not."""

        if self.active is False:
            return False

        if not isinstance(self.expires_at, datetime):
            raise TypeError("The 'expires_at' property should return a datetime!")

        if self.expires_at < datetime.now(timezone.utc):
            return True

        return False

    def scoped(self, scope: WorldCatScope) -> bool:
        """Support determining if the session has been authenticated for a scope."""

        if not self.active:
            self.authenticate()

        if not isinstance(scope, WorldCatScope):
            raise TypeError(
                "The 'scope' argument must reference a WorldCatScope enumeration option!"
            )

        if isinstance(self._authenticated_scopes, list):
            authenticated_scopes: set[str] = set()

            for authenticated_scope in self._authenticated_scopes:
                if ":" in authenticated_scope:
                    authenticated_scope, _ = authenticated_scope.split(":", maxsplit=1)
                authenticated_scopes.add(authenticated_scope)

            for authenticated_scope in authenticated_scopes:
                if reconciled := WorldCatScope.reconcile(authenticated_scope):
                    if reconciled is scope:
                        return True

        return False

    def authenticate(self) -> None:
        """Authenticate against WorldCat and store the authorization token for use
        during subsequent requests against the WorldCat API."""

        url: str = self._authendpoint

        logger.debug("%s.authenticate()" % (self.__class__.__name__))

        # If the session token has expired, reset the session state and re-authenticate:
        if self.expired is True:
            self.reset()

        if self.active is True:
            # If the Authorization header is missing from the session, restore it below:
            if not "Authorization" in self.headers:
                self.headers.update({"Authorization": f"Bearer {self._access_token}"})
        else:
            # Assemble the request headers for the authentication request
            headers = {"Accept": "application/json", "Content-Type": "application/json"}

            # Assemble the credentials into the format expected by WorldCat:
            credentials = (self._client_id, self._secret)

            # Specify the authentication grant type
            grant_type = "client_credentials"

            # Assemble the request parameters for the authentication request
            params = {
                "grant_type": grant_type,
                "scope": " ".join([str(scope) for scope in self._scopes]),
            }

            # Authenticate against WorldCat via this session's post() method; the request
            # is performed via the session (self) to ensure if this code is run through
            # the unit test suite with requests mocking enabled, that the request is mocked,
            # as request mocking is enabled through attaching the mocker to the session.

            # The HTTP request method functions supported by the WorldCatSession class,
            # such as self.get(), self.post() or self.put(), are the inherited directly
            # from the superclass – the requests library's Session class – and just like
            # the superclass, all are effectively aliases for self.request().

            # Our overridden implementation of self.request() adds key functionality to
            # the superclass' implementation, the most important of which is ensuring
            # that the session has been authenticated with WorldCat before performing
            # the specified request.

            # The authentication is handled by this method, as such, when self.post() is
            # called from this method, which as we know calls self.request(), we need to
            # ensure that the call to our overridden implementation of self.request()
            # does not result in a call back to this method, as that would result in an
            # infinite loop! We combine the need to avoid an infinite loop with the fact
            # that we do not want, nor could we, authenticate the authentication request
            # as trying to would result in a causality dilemma.

            # To prevent the infinite loop we pass in our custom 'authenticate' keyword
            # argument which our overridden implementation of self.request() acts on to
            # make the authentication request without first attempting to authenticate:
            response = self.post(
                url=url,
                auth=credentials,
                headers=headers,
                params=params,
                authenticate=False,
            )

            logger.debug(
                "%s.session(authentication) url => %s"
                % (self.__class__.__name__, response.url)
            )

            logger.debug(
                "%s.session(authentication) status => %s"
                % (self.__class__.__name__, response.status_code)
            )

            if response.status_code == 401:
                raise WorldCatAuthenticationError(
                    "WorldCat reported a [401 Unauthorized] error during authentication; ensure the credentials are valid!",
                    status_code=response.status_code,
                )

            response.raise_for_status()

            try:
                data: dict[str, object] = response.json()
            except Exception as exception:
                raise WorldCatAuthenticationError(
                    "WorldCat did not provide an expected JSON body response!",
                    status_code=response.status_code,
                ) from exception

            self._authenticated = True

            self._access_token = data.get("access_token")

            self._expires_at = datetime.strptime(
                data.get("expires_at"),
                "%Y-%m-%d %H:%M:%S%z",
            ).replace(tzinfo=timezone.utc)

            self._authenticating_institution_id = data.get(
                "authenticating_institution_id"
            )

            self._context_institution_id = data.get("context_institution_id")

            self._authenticated_scopes = (data.get("scopes") or "").split(" ")

            self._token_type = data.get("token_type")

            self._expires_in = data.get("expires_in")

            self._principal_id = data.get("principalID")

            self._principal_idns = data.get("principalIDNS")

            # Store the response cookies in the session for later use
            self.cookies = response.cookies.copy()

            # Store the access token in the session's headers for later use
            self.headers.update({"Authorization": f"Bearer {self._access_token}"})

    def reset(self) -> WorldCatSession:
        """Reset the session so that a new one can be created"""

        self._authenticated = False
        self._access_token = None
        self._expires_at = None
        self._authenticating_institution_id = None
        self._context_institution_id = None
        self._authenticated_scopes = None
        self._token_type = None
        self._expires_in = None
        self._principal_id = None
        self._principal_idns = None

        self.cookies.clear()
        self.headers.pop("Authorization", None)

        return self

    def request(
        self,
        method: str,
        url: str,
        *args,
        ignore: tuple[int] | int = None,
        authenticate: bool = True,
        retry: int = 0,
        **kwargs,
    ) -> requests.Response:
        """Wraps the requests' library's 'request' method allowing for improved handling
        of the request including handling authentication and token expiry and to better
        capture and handle failure responses generated by the WorldCat API including
        unauthorized requests."""

        if not isinstance(method, str):
            raise TypeError("The 'method' argument must have a string value!")
        elif not method in self._methods:
            raise ValueError(
                "The 'method' argument must have a HTTP method name value: %s!"
                % (", ".join(self._methods))
            )

        if not isinstance(url, str):
            raise TypeError("The 'url' argument must have a string value!")
        elif not url.startswith(self.endpoint):
            if not (url.startswith("http://") or url.startswith("https://")):
                url = self.endpoint.strip("/") + "/" + url.strip("/")

        if ignore is None:
            ignore: tuple[int] = tuple()
        elif isinstance(ignore, int):
            ignore: tuple[int] = tuple([ignore])

        if isinstance(ignore, tuple):
            for status in ignore:
                if not (isinstance(status, int) and not isinstance(status, bool)):
                    raise TypeError(
                        "The 'ignore' argument must only contain integer values!"
                    )
                elif not 100 <= status <= 599:
                    raise ValueError(
                        "The 'ignore' argument must only contain integer values in the range 100–599!"
                    )
        else:
            raise TypeError(
                "The 'ignore' argument, if specified, must have an integer or tuple of integers value!"
            )

        if not isinstance(authenticate, bool):
            raise TypeError("The 'authenticate' argument must have a boolean value!")

        # logger.debug(" >>> request method  => %s", method)
        # logger.debug(" >>> request url     => %s", url)

        if "timeout" not in kwargs:
            kwargs["timeout"] = DEFAULT_TIMEOUTS

        # Should the request be made with or without authentication?
        if authenticate is True:
            # Perform the HTTP request after authenticating the session:
            self.authenticate()
        elif authenticate is False:
            # Perform the HTTP request without authenticating the session, and ensure
            # that any previously set cookies or Authorization headers are removed:
            self.cookies.clear()
            self.headers.pop("Authorization", None)

        response = super().request(method, url, *args, **kwargs)

        logger.debug(
            "%s.request(method: %s, url: %s)",
            self.__class__.__name__,
            method,
            url,
        )

        data: object = None

        try:
            if "application/json" in (response.headers.get("Content-Type") or ""):
                if response.content and len(response.content) > 0:
                    data = response.json()
        except Exception as exception:
            logger.error("Unable to obtain data from response: %s", str(exception))

        # Handle ignored status codes, for cases we don't want to raise exceptions for
        if response.status_code in ignore:
            return response

        # Handle [200 OK ... 299] success responses
        elif 200 <= response.status_code <= 299:
            logger.debug(
                "%s.request[200...299](args: %s, method: %s, url: %s, retry: %s, kwargs: %s)",
                self.__class__.__name__,
                args,
                method,
                url,
                retry,
                kwargs,
            )

            return response

        # Handle [401 Unauthorized] responses
        # 401 Unauthorized responses can result from session timeouts as well as due to
        # invalid credentials, so the retry can resolve a timeout, but will not help for
        # invalid credentials which will need to be corrected manually.
        elif response.status_code == 401:
            logger.debug(
                "%s.request[401 Unauthorized](args: %s, method: %s, url: %s, retry: %s, kwargs: %s)",
                self.__class__.__name__,
                args,
                method,
                url,
                retry,
                kwargs,
            )

            # Reset the session, forcing a re-authentication on the next attempt
            self.reset()

            # If [401 Unauthorized] is reported during an authentication request, which
            # is noted via the authenticate argument being set to False, don't retry the
            # request, as the 401 status indicates that the credentials are invalid and
            # no number of retries will fix the issue; instead allow the authentication
            # method to process the response and handle it accordingly:
            if authenticate is False:
                return response

            if not isinstance(retry, int):
                raise TypeError("The 'retry' argument must have an integer value!")

            # If the maximum number of retries has not been reached, retry the request
            if retry < self.retries:
                return self.request(
                    method,
                    url,
                    *args,
                    ignore=ignore or None,
                    authenticate=authenticate,
                    retry=(retry + 1),
                    **kwargs,
                )
            else:
                raise WorldCatRequestError(
                    "The maximum number of retries has been reached for the request to: %s %s!"
                    % (
                        method,
                        url,
                    ),
                    status_code=401,
                )

        # Handle [404 Not Found] responses
        elif response.status_code == 404:
            logger.debug(
                "%s.request[404 Not Found](args: %s, method: %s, url: %s, retry: %s, kwargs: %s)",
                self.__class__.__name__,
                args,
                method,
                url,
                retry,
                kwargs,
            )

            return response

        # Handle [400 Bad Request] responses
        elif response.status_code == 400:
            logger.debug(
                "%s.request[400 Bad Request](args: %s, method: %s, url: %s, retry: %s, kwargs: %s) data => %r",
                self.__class__.__name__,
                args,
                method,
                url,
                retry,
                kwargs,
                data,
            )

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exception:
            message = str(exception)  # Capture the original HTTPError exception message

            logger.debug("-" * 50)
            for file, line, name in get_exception_locations(exception, all=True):
                logger.debug(" - %s(), %s, line %s", name, file, line)
            logger.debug("-" * 50)
            logger.debug("Request Method:   %s", response.request.method)
            logger.debug("Request URL:      %s", response.request.url)
            logger.debug("Request Body:     %s", response.request.body)
            logger.debug("Response Status:  %s", response.status_code)
            logger.debug("Response URL:     %s", response.url)
            logger.debug("Response Text:    %s", response.text)
            logger.debug("-" * 50)

            # Add the serialized JSON response body of the request (if any) to the
            # error message to provide additional context for any errors:
            if "application/json" in response.headers.get("Content-Type"):
                if isinstance(data := response.json(), (dict, list)):
                    message += " (" + json.dumps(data, ensure_ascii=False) + ")"

            # Now that we have added the JSON response (if there was one), we re-raise
            # the exception so that it may be captured downstream using 'from' to pass
            # in the current exception context to preserve the stack trace:
            raise requests.exceptions.HTTPError(message, response) from exception
        else:
            return response
