import pytest

from api_client.decorates import endpoint


@endpoint
class Endpoint:
    base_url = "http://foo.com"
    search = "search"
    integer = 3
    search_id = "search/{id}"
    _protected = "protected"


@endpoint
class EndpointWithExtraSlash:
    base_url = "http://foo.com///"
    search = "///search"


@endpoint()
class EndpointCalledWithParent:
    base_url = "http://foo.com"
    search = "search"


class EndpointNotDecorated:
    base_url = "http://foo.com"
    search = "search"


class EndpointMissingBaseUrl:
    search = "search"


def test_endpoint():
    assert Endpoint.search == "http://foo.com/search"
    assert Endpoint.integer == "http://foo.com/3"


def test_decorator_removes_traling_slashes_from_base_url():
    assert EndpointWithExtraSlash.search == "http://foo.com/search"


def test_calling_decorator_with_parenthesis():
    assert EndpointNotDecorated.search == "search"
    endpoint(EndpointNotDecorated)
    assert EndpointNotDecorated.search == "http://foo.com/search"


def test_endpoint_must_contain_base_url():
    with pytest.raises(RuntimeError) as exc_info:
        endpoint(EndpointMissingBaseUrl)
    assert str(exc_info.value) == "An Endpoint must define a `base_url`."


def test_endpoint_decorated_with_parens():
    assert Endpoint.search == "http://foo.com/search"


def test_endpoint_with_formatting():
    assert Endpoint.search_id == "http://foo.com/search/{id}"
    assert Endpoint.search_id.format(id=34) == "http://foo.com/search/34"


def test_decorator_does_not_modify_protected_attributes():
    assert Endpoint._protected == "protected"
