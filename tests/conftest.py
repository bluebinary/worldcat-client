import pytest
import requests
import requests_mock
import re
import json
import os
import sys
import time

# import multipart
# import io
import hashlib
import logging
import urllib

# from functools import cache

logger = logging.getLogger(__name__)

logger.debug("{loaded pytest configuration: %s}" % (__file__))

path = os.path.join(os.path.dirname(__file__), "..", "source")

sys.path.insert(0, path)

import worldcatclient

logger.debug("{loaded worldcatclient from: %s}" % (worldcatclient.__file__))

from worldcatclient.constants import (
    WORLDCAT_API_ENDPOINT,
    OCLC_AUTHENTICATION_ENDPOINT,
)

WORLDCAT_API_CLIENT_ID = os.getenv("WORLDCAT_API_CLIENT_ID") or "<client-id>"
WORLDCAT_API_SECRET = os.getenv("WORLDCAT_API_SECRET") or "<secret>"

# Override the default alphabetic sort of the test modules, into the order we wish to test
TEST_MODULE_ORDER = [
    "test_auth",
    "test_client",
]

DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), "data")


def pytest_collection_modifyitems(items):
    """Modifies test items in place to ensure test modules run in the given order."""

    module_mapping = {item: item.module.__name__ for item in items}

    sorted_items = items.copy()

    # Iteratively move tests of each module to the end of the test queue
    for module in TEST_MODULE_ORDER:
        sorted_items = [it for it in sorted_items if module_mapping[it] != module] + [
            it for it in sorted_items if module_mapping[it] == module
        ]

    items[:] = sorted_items


@pytest.fixture(name="client", scope="session")
def get_worldcat_client() -> worldcatclient.WorldCatClient:
    return worldcatclient.WorldCatClient(
        endpoint=WORLDCAT_API_ENDPOINT,
        client_id=WORLDCAT_API_CLIENT_ID,
        secret=WORLDCAT_API_SECRET,
    )


@pytest.fixture(scope="session", name="contents")
def contents() -> callable:
    """Create a fixture that can be used to obtain the contents of example data files as
    strings or bytes by specifying the path relative to the /tests/data folder."""

    def fixture(path: str, binary: bool = False) -> str:
        """Read the specified data file, returning its contents either as a string value
        or if requested in binary mode returning the encoded bytes value."""

        if not isinstance(path, str):
            raise TypeError("The 'path' argument must have a string value!")

        if not isinstance(binary, bool):
            raise TypeError("The 'binary' argument must have a boolean value!")

        if not path.endswith(".json"):
            path += ".json"

        filepath = os.path.join(os.path.dirname(__file__), "data", path)

        if not os.path.exists(filepath):
            raise ValueError(
                f"The requested example file, '{filepath}', does not exist!"
            )

        # If binary mode has been specified, adjust the read mode accordingly
        mode: str = "rb" if binary else "r"

        with open(filepath, mode) as handle:
            return handle.read()

    return fixture


@pytest.fixture(name="mocker", scope="session", autouse=True)
def mock_worldcat_api_fixture():
    """Mock the WorldCat API, so that we can return sample responses from the ./data directory"""

    with requests_mock.Mocker(real_http=True) as mocker:

        def mock_api_entries_callback(request, context):
            """Support mocking the WorldCat API requests, by intercepting requests
            to the WorldCat Client and providing static JSON file content provided
            as part of the test suite within the /tests/data/ subfolder."""

            # nonlocal mocker

            request.params = {}

            # Extract the individual request parameters from the request query string
            for param in request.query.split("&") if request.query else []:
                if len(parts := param.split("=", maxsplit=1)) == 2:
                    # request.params[parts[0]] = parts[1]
                    pass

            # Ensure that the request parameters are not duplicated in the URL string
            if "?" in request.url:
                if query := request.url.split("?", maxsplit=1)[1]:
                    for param in query.split("&"):
                        if len(parts := param.split("=", maxsplit=1)) == 2:
                            if parts[0] in request.params:
                                if request.params[parts[0]] == parts[1]:
                                    del request.params[parts[0]]

            logger.debug("Request Method:   %r" % (request.method))
            logger.debug("Request URL:      %r" % (request.url))
            logger.debug("Request URL Path: %r" % (request.path_url))
            logger.debug("Request Query:    %r" % (request.query))
            logger.debug("Request Params:   %r" % (request.params))
            logger.debug("Request Headers:  %r" % (request.headers))
            logger.debug("Request Query:    %r" % (request.query))
            logger.debug("Request Params:   %r" % (request.params))
            logger.debug("Request Body:     %r" % (request.body))
            logger.debug("Request Text:     %r" % (request.text))
            logger.debug(
                "Request Timeout:  %r"
                % (
                    list(request.timeout)
                    if isinstance(request.timeout, tuple)
                    else request.timeout
                )
            )
            logger.debug("Mock (Case Sensitive): %r" % (mocker.case_sensitive))

            if "?" in request.path_url:
                request.path_url = request.path_url.split("?")[0]

            is_list_endpoint = (request.path_url.endswith("/list") is True) or False

            filepath = os.path.realpath(
                os.path.join(
                    DATA_DIRECTORY,
                    "responses",
                    urllib.parse.urlunparse(
                        urllib.parse.urlparse(request.url)._replace(scheme="", query="")
                    ).strip("/"),
                )
            )

            if not os.path.isdir(filepath):
                os.makedirs(filepath, 0o777, exist_ok=True)

            filehash = hashlib.md5()

            filehash.update(request.method.encode("utf-8"))

            if request.headers:
                filehash.update(
                    ";".join(
                        [
                            f"{key}: {value}"
                            for key, value in request.headers.items()
                            if not key
                            in [
                                "Accept-Encoding",
                                "Authorization",
                                "User-Agent",
                            ]
                        ]
                    ).encode("utf-8")
                )

            if request.query:
                filehash.update(request.query.encode("utf-8"))

            filepath = os.path.join(filepath, filehash.hexdigest() + ".json")

            logger.debug(
                "Request File:     %s (Exists: %s)"
                % (filepath, "Yes" if os.path.isfile(filepath) else "No")
            )

            if not os.path.isfile(filepath):
                # Temporarily stop mocking so that we can communicate with the server
                mocker.stop()

                # Perform a real HTTP request against the server
                response = requests.request(
                    method=request.method,
                    url=request.url,
                    params=request.params,
                    headers=request.headers,
                    data=request.body,
                )

                # Log the details of the response
                logger.debug("JSON File Path: %s", filepath)
                logger.debug("HTTP URL:       %s", response.request.url)
                logger.debug("HTTP Headers:   %s", response.request.headers)
                logger.debug("HTTP Status:    %s", response.status_code)
                logger.debug("HTTP Headers:   %s", response.headers)
                logger.debug("HTTP Encoding:  %s", response.encoding)
                logger.debug(
                    "HTTP Content:   %s",
                    (
                        response.content
                        if response.content and len(response.content) < 10000
                        else "TOO LONG"
                    ),
                )

                # Restart mocking
                mocker.start()

                # Cache the captured response for future mocked requests
                with open(filepath, "w+") as file:
                    if response.headers and "application/json" in response.headers.get(
                        "Content-Type", ""
                    ):
                        data = json.loads(response.content)
                        data = json.dumps(data, indent=2).encode("utf-8")
                    else:
                        data = response.content

                    if isinstance(data, (dict, list)):
                        mocker.data = data
                    else:
                        mocker.data = None

                    headers = dict(response.request.headers)

                    if "Authorization" in headers:
                        headers["Authorization"] = "Bearer <token>"

                    payload = dict(
                        method=response.request.method,
                        url=response.request.url,
                        params=request.params,
                        headers=headers,
                        status_code=response.status_code,
                        type=response.headers.get("Content-Type")
                        or "application/octet-stream",
                        content=response.content.decode("utf-8"),
                    )

                    json.dump(payload, file, indent=2, ensure_ascii=False)

            # If no cached response exists even after trying, return a 500 error
            if not os.path.isfile(filepath):
                context.status_code = 500
                return None

            # Return the cached response when it exists
            with open(filepath, "r") as handle:
                if isinstance(cached := json.load(handle), dict):
                    # simulate a connection/read timeout by throwing the exception
                    if (delay := float(request.params.get("delay") or 0)) > 0:
                        time.sleep(delay)

                        if isinstance(request.timeout, (float, tuple)):
                            if isinstance(request.timeout, tuple):
                                timeout = request.timeout[1]
                            else:
                                timeout = request.timeout

                            if timeout < delay:
                                raise requests.exceptions.ReadTimeout(
                                    "The mocked request timed-out!"
                                )

                    if status_code := cached.get("status_code"):
                        context.status_code = status_code
                    else:
                        context.status_code = 500

                    if content := cached.get("content"):
                        mocker.data = json.loads(content)
                    else:
                        mocker.data = None

                    if is_list_endpoint:
                        context.headers.update(
                            {
                                "Content-Type": "text/plain;charset=UTF-8",
                                "Content-Length": str(len(content)),
                            }
                        )
                    else:
                        context.headers.update(
                            {
                                "Content-Type": "application/json;charset=UTF-8",
                                "Content-Length": str(len(content)),
                            }
                        )

                    if headers := cached.get("headers"):
                        context.headers.update(headers)

                    logger.debug("HTTP Content:  %s", str(type(content)))

                    return content

            context.status_code = 404

            return None

        # Define the URL pattern to override through the mocker
        # <base-url>/query?<query-string-parameters>
        query_pattern = re.compile(WORLDCAT_API_ENDPOINT + r"/query(?P<params>\?.*)?")

        # Register the mocker against the expected HTTP methods
        mocker.head(query_pattern, text=mock_api_entries_callback)
        mocker.get(query_pattern, text=mock_api_entries_callback)
        mocker.post(query_pattern, text=mock_api_entries_callback)
        mocker.put(query_pattern, text=mock_api_entries_callback)
        mocker.delete(query_pattern, text=mock_api_entries_callback)

        # Define the URL pattern to override through the mocker
        # <base-url>/path?<query-string-parameters>
        cache_pattern = re.compile(
            WORLDCAT_API_ENDPOINT + r"(?P<path>/.*?)(?P<params>\?.*)?"
        )

        # Register the mocker against the expected HTTP methods
        mocker.head(cache_pattern, text=mock_api_entries_callback)
        mocker.get(cache_pattern, text=mock_api_entries_callback)
        mocker.post(cache_pattern, text=mock_api_entries_callback)
        mocker.put(cache_pattern, text=mock_api_entries_callback)
        mocker.delete(cache_pattern, text=mock_api_entries_callback)

        # Define the URL pattern to override through the mocker
        auth_pattern = re.compile(OCLC_AUTHENTICATION_ENDPOINT)

        # Register the mocker against the expected HTTP methods
        mocker.head(auth_pattern, text=mock_api_entries_callback)
        mocker.get(auth_pattern, text=mock_api_entries_callback)
        mocker.post(auth_pattern, text=mock_api_entries_callback)
        mocker.put(auth_pattern, text=mock_api_entries_callback)
        mocker.delete(auth_pattern, text=mock_api_entries_callback)

        yield mocker
