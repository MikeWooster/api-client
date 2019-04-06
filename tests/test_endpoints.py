import os

import pytest

from apiclient import endpoint


@endpoint(base_url="http://foo.com")
class Endpoint:
    search = "search"
    integer = 3
    search_id = "search/{id}"
    _protected = "protected"


@endpoint(base_url="http://foo.com///")
class EndpointWithExtraSlash:
    search = "///search"


class EndpointNotDecorated:
    search = "search"


@endpoint(base_url=os.environ["ENDPOINT_BASE_URL"])
class EndpointFromEnvironment:
    search = "search"


def test_endpoint():
    assert Endpoint.search == "http://foo.com/search"
    assert Endpoint.integer == "http://foo.com/3"


def test_decorator_removes_trailing_slashes_from_base_url():
    assert EndpointWithExtraSlash.search == "http://foo.com/search"


def test_endpoint_must_contain_base_url():
    with pytest.raises(RuntimeError) as exc_info:
        endpoint(EndpointNotDecorated)
    expected_message = "A decorated endpoint must define a base_url as @endpoint(base_url='http://foo.com')."
    assert str(exc_info.value) == expected_message


def test_endpoint_with_formatting():
    assert Endpoint.search_id == "http://foo.com/search/{id}"
    assert Endpoint.search_id.format(id=34) == "http://foo.com/search/34"


def test_decorator_does_not_modify_protected_attributes():
    assert Endpoint._protected == "protected"


def test_decorated_endpoint_loaded_from_environment_variable():
    assert EndpointFromEnvironment.search == "http://environment.com/search"
