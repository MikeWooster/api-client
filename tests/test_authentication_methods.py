import http.cookiejar

import pytest

from apiclient import (
    APIClient,
    BasicAuthentication,
    HeaderAuthentication,
    NoAuthentication,
    QueryParameterAuthentication,
)
from apiclient.authentication_methods import CookieAuthentication
from apiclient.request_formatters import BaseRequestFormatter, NoOpRequestFormatter
from apiclient.response_handlers import BaseResponseHandler, RequestsResponseHandler


def test_no_authentication_method_does_not_alter_client():
    client = APIClient(
        authentication_method=NoAuthentication(),
        response_handler=BaseResponseHandler,
        request_formatter=BaseRequestFormatter,
    )
    assert client.get_default_query_params() == {}
    assert client.get_default_headers() == {}
    assert client.get_default_username_password_authentication() is None


def test_query_parameter_authentication_alters_client_default_query_parameters():
    client = APIClient(
        authentication_method=QueryParameterAuthentication(parameter="apikey", token="secret"),
        response_handler=BaseResponseHandler,
        request_formatter=BaseRequestFormatter,
    )
    assert client.get_default_query_params() == {"apikey": "secret"}
    assert client.get_default_headers() == {}
    assert client.get_default_username_password_authentication() is None


def test_header_authentication_with_default_values():
    client = APIClient(
        authentication_method=HeaderAuthentication(token="secret"),
        response_handler=BaseResponseHandler,
        request_formatter=BaseRequestFormatter,
    )
    assert client.get_default_query_params() == {}
    assert client.get_default_headers() == {"Authorization": "Bearer secret"}
    assert client.get_default_username_password_authentication() is None


def test_header_authentication_overwriting_scheme():
    client = APIClient(
        authentication_method=HeaderAuthentication(token="secret", scheme="Token"),
        response_handler=BaseResponseHandler,
        request_formatter=BaseRequestFormatter,
    )
    assert client.get_default_query_params() == {}
    assert client.get_default_headers() == {"Authorization": "Token secret"}
    assert client.get_default_username_password_authentication() is None


def test_header_authentication_overwriting_parameter():
    client = APIClient(
        authentication_method=HeaderAuthentication(token="secret", parameter="APIKEY"),
        response_handler=BaseResponseHandler,
        request_formatter=BaseRequestFormatter,
    )
    assert client.get_default_query_params() == {}
    assert client.get_default_headers() == {"APIKEY": "Bearer secret"}
    assert client.get_default_username_password_authentication() is None


@pytest.mark.parametrize("scheme", [None, "", 0])
def test_scheme_is_not_included_when_evaluates_to_false(scheme):
    client = APIClient(
        authentication_method=HeaderAuthentication(token="secret", parameter="APIKEY", scheme=scheme),
        response_handler=BaseResponseHandler,
        request_formatter=BaseRequestFormatter,
    )
    assert client.get_default_query_params() == {}
    assert client.get_default_headers() == {"APIKEY": "secret"}
    assert client.get_default_username_password_authentication() is None


def test_basic_authentication_alters_client():
    client = APIClient(
        authentication_method=BasicAuthentication(username="uname", password="password"),
        response_handler=BaseResponseHandler,
        request_formatter=BaseRequestFormatter,
    )
    assert client.get_default_query_params() == {}
    assert client.get_default_headers() == {}
    assert client.get_default_username_password_authentication() == ("uname", "password")


def test_cookie_authentication_makes_request_on_client_initialization(mock_requests):
    cookiejar = http.cookiejar.CookieJar()
    mocker = mock_requests.get("http://example.com/authenticate", status_code=200, cookies=cookiejar)

    APIClient(
        authentication_method=CookieAuthentication(
            auth_url="http://example.com/authenticate", authentication=HeaderAuthentication(token="foo")
        ),
        response_handler=RequestsResponseHandler,
        request_formatter=NoOpRequestFormatter,
    )
    assert mocker.called
    assert mocker.call_count == 1
    # TODO: is there a way we can test the cookiejar contents after making the request?
