# WorldCat Client

The WorldCat Client library for Python provides a simplified way to interact with the
WorldCat API and includes support for authentication and session handling, as well as
the querying and parsing of certain data sets held in WorldCat.

### Requirements

The WorldCat Client library has been tested with Python 3.10, 3.11, 3.12, 3.13 and 3.14.
The library was not designed to work with Python 3.9 or earlier.

### Installation

The WorldCat Client library is available from the PyPi repository, so may be added to a project's dependencies via its `requirements.txt` file or similar by referencing the WorldCat Client library's name, `worldcatclient`, or the library may be installed directly onto your local development system using `pip install` by entering the following command:

	$ pip install worldcatclient

### Usage

The WorldCat Client library provides the `WorldCatClient` class which can be used to interact
with the supported WorldCat API services.

The instantiation of the client is very simple. The examples shown below in the [**Client Instantiation & Setup**](#client-initialisation-setup) section show the basic instantiation of the WorldCat Client, and also some basic error handling, highlighting the different custom exceptions supported by the client.

<a name="client-methods"></a>
### Client Methods

The the following methods are provided by the client:

* `search(...)` (`Iterator[dict[str, object]]` | `Iterator[WorldCatRecord]`) – this method is used to search via the WorldCat Search API for brief bibliographic records, and yields the record results through an iterator. The method accepts the following keyword arguments:

    * `query` (`str`) – (required) use to specify the search query.
    * `limit` (`int`) – (optional) used to specify the maximum number of search results to obtain per API call; defaults to `10`; if specified must have a value between `1` – `50` results.
    * `parsed` (`bool`) – (optional) use to control whether the `.search()` method returns raw dictionary record payloads or a parsed record payload as `WorldCatRecord` class instances; defaults to `False`, set to `True` to return parsed record payloads.
    * `order` (`WorldCatOrderingSearchAPI`) - (optional) use to specify the sort order for the search results; defaults to `WorldCatOrderingSearchAPI.BestMatch`, but can be set to any of the available `WorldCatOrderingSearchAPI` enumeration options. See [**Sort Order**](#sort-order) below.
    * `timeout` (`int`) – (optional) used to specify the maximum timeout for the API call; defaults to `10`; if specified must have a value between `1` – `120` seconds.
    * `offset` (`int`) – (optional) used internally by the method to support paginating through the results; defaults to `None`; if specified must have a value `1+`; should not be specified manually.

<a name="client-initialisation-setup"></a>
### Client Initialisation & Setup

The example illustrates initialising the `WorldCatClient`, providing the required parameters,
then demonstrates use of the various methods of the client to perform the supported operations:

<!--pytest.mark.skip-->

```python
from worldcatclient import WorldCatClient

# Initialise the client, supplying the token, and any desired optional parameters:
client = WorldCatClient(
    client_id = "<token>",
    secret = "<secret>",
)

# Query the WorldCat API and do something with the results:
for record in client.search(query="ti:WorldCat API"):
    assert isinstance(record, dict)

    print(record)
```

<a name="search-result-model"></a>
### Records

The WorldCat Client can return both raw search result records payloads as well as an
instance of its `WorldCatRecord` class which simplifies the process of interfacing with
the search result records by parsing the record payload into an Python class with
properties to access each value.

To perform a search and to have the `WorldCatClient` return `WorldCatRecord` class
instances instead of the raw search result record payloads, simply pass the optional
`parsed` argument to the `.search()` method with a value of `True`:

<!--pytest.mark.skip-->

```python
from worldcatclient import WorldCatClient, WorldCatRecord

client = WorldCatClient(
    client_id = "<token>",
    secret = "<secret>",
)

# Query the WorldCat API and do something with the results:
for record in client.search(query="ti:WorldCat API", parsed=True):
    assert isinstance(record, WorldCatRecord)

    print(record)
```

<a name="sort-order"></a>
### Search Results Sort Order

The sort order of the search results can be modified from their default sort order of
"best match", by specifying the `order` keyword argument when calling the `.search()`
method, and specifying one of the available `WorldCatOrderingSearchAPI` enumeration
options. The available options are as follows:

| Enumeration Option    | Description                           |
|-----------------------|---------------------------------------|
| `Library`             | Sort by library                       |
| `Recency`             | Sort by recency                       |
| `BestMatch`           | Sort by best match (the default)      |
| `Creator`             | Sort by creator                       |
| `PublicationDateAsc`  | Sort by publication date (ascending)  |
| `PublicationDateDesc` | Sort by publication date (descending) |
| `MostWidelyHeld`      | Sort by most widely held              |
| `Title`               | Sort by most title                    |

For example to search and sort by recency, the `.search()` method would be called as
shown below:

<!--pytest.mark.skip-->

```python
from worldcatclient import WorldCatClient, WorldCatRecord, WorldCatOrderingSearchAPI

client = WorldCatClient(
    client_id = "<token>",
    secret = "<secret>",
)

# Query the WorldCat API and do something with the results:
for record in client.search(
    query="ti:WorldCat API",
    order=WorldCatOrderingSearchAPI.Recency,
    parsed=True,
):
    assert isinstance(record, WorldCatRecord)

    print(record)
```

<a name="code-formatting"></a>
### Code Formatting

The WorldCat Client library adheres to the code formatting specifications set out in PEP-8, which are verified and applied by the _Black_ code formatting tool. Whenever code changes are made to the library, one needs to ensure that the code conforms to these code formatting specifications. To simplify this, the provided `Dockerfile` creates an image that supports running the _Black_ code formatting tool against the latest version of the code, and will report back if any issues are found. To run the code formatting checks, perform the following commands, which will build the Docker image via `docker compose build` and then run the tests via `docker compose run black` – the output of running the formatting checks will be displayed:

```shell
$ docker compose build
$ docker compose run black
```

If any code formatting issues are found, it is possible to run _Black_ so that it will automatically reformat the affected files; this can be achieved as follows:

```shell
$ docker compose run black --reformat
```

The above will reformat any files that contained code formatting issues, and will report back on what changes were made; once the code has been automatically reformatted, it will continue to pass the formatting checks until any future code changes that fall outside of the PEP-8 and _Black_ code formatting specifications.

<a name="code-linting"></a>
### Code Linting

The WorldCat Client library adheres to the code linting specifications set out in PEP-8, which are verified and applied by the _PyFlakes_ code linting tool. Whenever code changes are made to the library, one needs to ensure that the code conforms to these code formatting specifications. To simplify this, the provided `Dockerfile` creates an image that supports running the _PyFlakes_ code linting tool against the latest version of the code, and will report back if any issues are found. To run the code linting checks, perform the following commands, which will build the Docker image via `docker compose build` and then run the tests via `docker compose run flakes` – the output of running the linting checks will be displayed:

```shell
$ docker compose build
$ docker compose run flakes
```

If any code linting issues are found, such as references to undefined names, or unused imports, each issue will need to be addressed by making the necessary code changes and re-testing with `PyFlakes`, before the library changes can be submitted for review.

<a name="unit-tests"></a>
### Unit Tests

The WorldCat Client library includes a suite of comprehensive unit tests which ensure that the library functionality operates as expected, including testing and validating client instantiation, entry retrieval, creation, updating, publishing, un-publishing, and deletion. The unit tests were developed with and run via `pytest`.

To ensure that the unit tests are run within a predictable runtime environment where all of the necessary dependencies are available, a Docker image is created within which the tests are run. To run the unit tests, perform the following commands, which will build the Docker image via `docker compose build` and then run the tests via `docker compose run tests` – the output of running the tests will be displayed:

```shell
$ docker compose build
$ docker compose run tests
```

To run the unit tests with optional command line arguments being passed to `pytest`, append the relevant arguments to the `docker compose run tests` command, as follows, for example passing `-vv` to enable verbose output:

```shell
$ docker compose run tests -vv
```

It is also possible to view additional output from the test suite by running the tests with the `-s` command line flag, which captures standard output from any running code and emits it into the terminal for review.

```shell
$ docker compose run tests -vv -s
```

Additionally, if you wish to just run a single unit test, say for a new feature being developed, the `-k` command line flag can be used to filter the unit tests that will be run, where you can specify a range of values to the option, including the name of the unit test function or file that you want to use:

```shell
$ docker compose run tests -vv -s -k test_client_initialisation
```

See the documentation for [PyTest](https://docs.pytest.org/en/latest/) regarding available optional command line arguments.

### Copyright & License Information

Copyright © 2026 Daniel Sissman; licensed under the MIT License.