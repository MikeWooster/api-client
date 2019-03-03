import logging
from http import HTTPStatus
from unittest.mock import Mock, patch, sentinel

import pytest

from apiclient import exceptions
from apiclient.authentication_methods import NoAuthentication
from apiclient.client import LOG as client_logger
from apiclient.client import BaseClient
from apiclient.exceptions import ClientError, RedirectionError, ServerError, UnexpectedError
from apiclient.request_formatters import BaseRequestFormatter, JsonRequestFormatter
from apiclient.response_handlers import BaseResponseHandler, JsonResponseHandler


# Minimal client - no implementation
class Client(BaseClient):
    pass


# Real world api client with GET methods implemented.
class JSONPlaceholderClient(BaseClient):
    base_url = "https://jsonplaceholder.typicode.com"

    def get_all_todos(self) -> dict:
        url = f"{self.base_url}/todos"
        return self.read(url)

    def get_todo(self, todo_id: int) -> dict:
        url = f"{self.base_url}/todos/{todo_id}"
        return self.read(url)


mock_response_handler_call = Mock()
mock_request_formatter_call = Mock()


class MockResponseHandler(BaseResponseHandler):
    """Mock class for testing."""

    @staticmethod
    def get_request_data(response):
        mock_response_handler_call(response)
        return response


class MockRequestFormatter(BaseRequestFormatter):
    """Mock class for testing."""

    @classmethod
    def format(cls, data: dict):
        mock_request_formatter_call(data)
        return data


client = Client(
    authentication_method=NoAuthentication(),
    response_handler=MockResponseHandler,
    request_formatter=MockRequestFormatter,
)


def test_client_initialization_with_invalid_authentication_method():
    with pytest.raises(RuntimeError) as exc_info:
        Client(
            authentication_method=None,
            response_handler=MockResponseHandler,
            request_formatter=MockRequestFormatter,
        )
    expected_message = "provided authentication_method must be an instance of BaseAuthenticationMethod."
    assert str(exc_info.value) == expected_message


def test_client_initialization_with_invalid_response_handler():
    with pytest.raises(RuntimeError) as exc_info:
        Client(
            authentication_method=NoAuthentication(),
            response_handler=None,
            request_formatter=MockRequestFormatter,
        )
    assert str(exc_info.value) == "provided response_handler must be a subclass of BaseResponseHandler."


def test_client_initialization_with_invalid_requests_handler():
    with pytest.raises(RuntimeError) as exc_info:
        Client(
            authentication_method=NoAuthentication(),
            response_handler=MockResponseHandler,
            request_formatter=None,
        )
    assert str(exc_info.value) == "provided request_formatter must be a subclass of BaseRequestFormatter."


def test_set_and_get_default_headers():
    client = Client(
        authentication_method=NoAuthentication(),
        response_handler=MockResponseHandler,
        request_formatter=MockRequestFormatter,
    )
    assert client.get_default_headers() == {}
    client.set_default_headers({"first": "header"})
    assert client.get_default_headers() == {"first": "header"}
    # Setting the default headers should overwrite the original
    client.set_default_headers({"second": "header"})
    assert client.get_default_headers() == {"second": "header"}


def test_set_and_get_default_query_params():
    client = Client(
        authentication_method=NoAuthentication(),
        response_handler=MockResponseHandler,
        request_formatter=MockRequestFormatter,
    )
    assert client.get_default_query_params() == {}
    client.set_default_query_params({"first": "header"})
    assert client.get_default_query_params() == {"first": "header"}
    # Setting the default query params should overwrite the original
    client.set_default_query_params({"second": "header"})
    assert client.get_default_query_params() == {"second": "header"}


def test_set_and_get_default_username_password_authentication():
    client = Client(
        authentication_method=NoAuthentication(),
        response_handler=MockResponseHandler,
        request_formatter=MockRequestFormatter,
    )
    assert client.get_default_username_password_authentication() is None
    client.set_default_username_password_authentication(("username", "password"))
    assert client.get_default_username_password_authentication() == ("username", "password")
    # Setting the default username password should overwrite the original
    client.set_default_username_password_authentication(("username", "morecomplicatedpassword"))
    assert client.get_default_username_password_authentication() == ("username", "morecomplicatedpassword")


@patch("apiclient.client.requests")
def test_create_method_success(mock_requests):
    mock_requests.post.return_value.status_code = 201
    client.create(sentinel.url, data={"foo": "bar"})
    mock_requests.post.assert_called_once_with(
        sentinel.url, auth=None, headers={}, data={"foo": "bar"}, params={}
    )


@patch("apiclient.client.requests")
def test_read_method_success(mock_requests):
    mock_requests.get.return_value.status_code = 200
    client.read(sentinel.url)
    mock_requests.get.assert_called_once_with(sentinel.url, auth=None, headers={}, params={}, data=None)


@patch("apiclient.client.requests")
def test_replace_method_success(mock_requests):
    mock_requests.put.return_value.status_code = 200
    client.replace(sentinel.url, data={"foo": "bar"})
    mock_requests.put.assert_called_once_with(
        sentinel.url, auth=None, headers={}, data={"foo": "bar"}, params={}
    )


@patch("apiclient.client.requests")
def test_update_method_success(mock_requests):
    mock_requests.patch.return_value.status_code = 200
    client.update(sentinel.url, data={"foo": "bar"})
    mock_requests.patch.assert_called_once_with(
        sentinel.url, auth=None, headers={}, data={"foo": "bar"}, params={}
    )


@patch("apiclient.client.requests")
def test_delete_method_success(mock_requests):
    mock_requests.delete.return_value.status_code = 200
    client.delete(sentinel.url)
    mock_requests.delete.assert_called_once_with(sentinel.url, auth=None, headers={}, params={}, data=None)


@pytest.mark.parametrize(
    "client_method,client_args,patch_methodname",
    [
        (client.create, (sentinel.url, {"foo": "bar"}), "apiclient.client.requests.post"),
        (client.read, (sentinel.url,), "apiclient.client.requests.get"),
        (client.replace, (sentinel.url, {"foo": "bar"}), "apiclient.client.requests.put"),
        (client.update, (sentinel.url, {"foo": "bar"}), "apiclient.client.requests.patch"),
        (client.delete, (sentinel.url,), "apiclient.client.requests.delete"),
    ],
)
def test_make_request_error_raises_and_logs_unexpected_error(
    client_method, client_args, patch_methodname, caplog
):
    caplog.set_level(level=logging.ERROR, logger=client_logger.name)
    with patch(patch_methodname) as mock_requests_method:
        mock_requests_method.side_effect = (ValueError("Error raised for testing"),)
        with pytest.raises(UnexpectedError) as exc_info:
            client_method(*client_args)
    assert str(exc_info.value) == "Error when contacting 'sentinel.url'"
    messages = [r.message for r in caplog.records if r.levelno == logging.ERROR]
    assert "An error occurred when contacting sentinel.url" in messages


@pytest.mark.parametrize(
    "client_method,client_args,patch_methodname",
    [
        (client.create, (sentinel.url, {"foo": "bar"}), "apiclient.client.requests.post"),
        (client.read, (sentinel.url,), "apiclient.client.requests.get"),
        (client.replace, (sentinel.url, {"foo": "bar"}), "apiclient.client.requests.put"),
        (client.update, (sentinel.url, {"foo": "bar"}), "apiclient.client.requests.patch"),
        (client.delete, (sentinel.url,), "apiclient.client.requests.delete"),
    ],
)
def test_server_error_raises_and_logs_client_server_error(
    client_method, client_args, patch_methodname, caplog
):
    caplog.set_level(level=logging.WARNING, logger=client_logger.name)
    with patch(patch_methodname) as mock_requests_method:
        mock_requests_method.return_value.status_code = 500
        mock_requests_method.return_value.url = sentinel.url
        mock_requests_method.return_value.reason = "A TEST server error occurred"
        mock_requests_method.return_value.text = "{'foo': 'bar'}"

        with pytest.raises(ServerError) as exc_info:
            client_method(*client_args)
    assert str(exc_info.value) == "500 Error: A TEST server error occurred for url: sentinel.url"
    messages = [r.message for r in caplog.records if r.levelno == logging.WARNING]
    assert "500 Error: A TEST server error occurred for url: sentinel.url. data={'foo': 'bar'}" in messages


@pytest.mark.parametrize(
    "client_method,client_args,patch_methodname",
    [
        (client.create, (sentinel.url, {"foo": "bar"}), "apiclient.client.requests.post"),
        (client.read, (sentinel.url,), "apiclient.client.requests.get"),
        (client.replace, (sentinel.url, {"foo": "bar"}), "apiclient.client.requests.put"),
        (client.update, (sentinel.url, {"foo": "bar"}), "apiclient.client.requests.patch"),
        (client.delete, (sentinel.url,), "apiclient.client.requests.delete"),
    ],
)
def test_not_modified_response_raises_and_logs_client_redirection_error(
    client_method, client_args, patch_methodname, caplog
):
    caplog.set_level(level=logging.ERROR, logger=client_logger.name)
    with patch(patch_methodname) as mock_requests_method:
        mock_requests_method.return_value.status_code = 304
        mock_requests_method.return_value.url = sentinel.url
        mock_requests_method.return_value.reason = "A TEST redirection error occurred"
        mock_requests_method.return_value.text = "{'foo': 'bar'}"

        with pytest.raises(RedirectionError) as exc_info:
            client_method(*client_args)
    assert str(exc_info.value) == "304 Error: A TEST redirection error occurred for url: sentinel.url"
    messages = [r.message for r in caplog.records if r.levelno == logging.ERROR]
    assert (
        "304 Error: A TEST redirection error occurred for url: sentinel.url. data={'foo': 'bar'}" in messages
    )


@pytest.mark.parametrize(
    "client_method,client_args,patch_methodname",
    [
        (client.create, (sentinel.url, {"foo": "bar"}), "apiclient.client.requests.post"),
        (client.read, (sentinel.url,), "apiclient.client.requests.get"),
        (client.replace, (sentinel.url, {"foo": "bar"}), "apiclient.client.requests.put"),
        (client.update, (sentinel.url, {"foo": "bar"}), "apiclient.client.requests.patch"),
        (client.delete, (sentinel.url,), "apiclient.client.requests.delete"),
    ],
)
def test_not_found_response_raises_and_logs_client_bad_request_error(
    client_method, client_args, patch_methodname, caplog
):
    caplog.set_level(level=logging.ERROR, logger=client_logger.name)
    with patch(patch_methodname) as mock_requests_method:
        mock_requests_method.return_value.status_code = 404
        mock_requests_method.return_value.url = sentinel.url
        mock_requests_method.return_value.reason = "A TEST not found error occurred"
        mock_requests_method.return_value.text = "{'foo': 'bar'}"

        with pytest.raises(ClientError) as exc_info:
            client_method(*client_args)
    assert str(exc_info.value) == "404 Error: A TEST not found error occurred for url: sentinel.url"
    messages = [r.message for r in caplog.records if r.levelno == logging.ERROR]
    assert (
        "404 Error: A TEST not found error occurred for url: sentinel.url. data={'foo': 'bar'}" in messages
    )


@pytest.mark.parametrize(
    "client_method,client_args,patch_methodname",
    [
        (client.create, (sentinel.url, {"foo": "bar"}), "apiclient.client.requests.post"),
        (client.read, (sentinel.url,), "apiclient.client.requests.get"),
        (client.replace, (sentinel.url, {"foo": "bar"}), "apiclient.client.requests.put"),
        (client.update, (sentinel.url, {"foo": "bar"}), "apiclient.client.requests.patch"),
        (client.delete, (sentinel.url,), "apiclient.client.requests.delete"),
    ],
)
def test_unexpected_status_code_response_raises_and_logs_unexpected_error(
    client_method, client_args, patch_methodname, caplog
):
    caplog.set_level(level=logging.ERROR, logger=client_logger.name)
    with patch(patch_methodname) as mock_requests_method:
        mock_requests_method.return_value.status_code = 100
        mock_requests_method.return_value.url = sentinel.url
        mock_requests_method.return_value.reason = "A TEST bad status code error occurred"
        mock_requests_method.return_value.text = "{'foo': 'bar'}"

        with pytest.raises(UnexpectedError) as exc_info:
            client_method(*client_args)
    assert str(exc_info.value) == "100 Error: A TEST bad status code error occurred for url: sentinel.url"
    messages = [r.message for r in caplog.records if r.levelno == logging.ERROR]
    expected_log_message = (
        "100 Error: A TEST bad status code error occurred for url: sentinel.url. " "data={'foo': 'bar'}"
    )
    assert expected_log_message in messages


@pytest.mark.parametrize(
    "client_method,client_args,patch_methodname",
    [
        (client.read, (sentinel.url,), "apiclient.client.requests.get"),
        (client.replace, (sentinel.url, {"foo": "bar"}), "apiclient.client.requests.put"),
        (client.update, (sentinel.url, {"foo": "bar"}), "apiclient.client.requests.patch"),
        (client.delete, (sentinel.url,), "apiclient.client.requests.delete"),
    ],
)
def test_query_params_are_updated_and_not_overwritten(client_method, client_args, patch_methodname):
    # Params are not expected on POST endpoints, so this method is not placed under test.
    with patch(patch_methodname) as mock_requests_method:
        mock_requests_method.return_value.status_code = 200

        client_method(*client_args, params={"New": "Header"})

    assert mock_requests_method.call_count == 1
    args, kwargs = mock_requests_method.call_args
    assert "params" in kwargs
    assert kwargs["params"]["New"] == "Header"


@pytest.mark.parametrize(
    "client_method,client_args,patch_methodname",
    [
        (client.create, (sentinel.url, {"foo": "bar"}), "apiclient.client.requests.post"),
        (client.read, (sentinel.url,), "apiclient.client.requests.get"),
        (client.replace, (sentinel.url, {"foo": "bar"}), "apiclient.client.requests.put"),
        (client.update, (sentinel.url, {"foo": "bar"}), "apiclient.client.requests.patch"),
        (client.delete, (sentinel.url,), "apiclient.client.requests.delete"),
    ],
)
def test_delegates_to_response_handler(client_method, client_args, patch_methodname):
    mock_response_handler_call.reset_mock()

    with patch(patch_methodname) as mock_requests_method:
        requests_response = Mock(status_code=200)
        mock_requests_method.return_value = requests_response

        client_method(*client_args)

    mock_response_handler_call.assert_called_once_with(requests_response)


@pytest.mark.parametrize(
    "client_method,url,patch_methodname",
    [
        (client.create, sentinel.url, "apiclient.client.requests.post"),
        (client.replace, sentinel.url, "apiclient.client.requests.put"),
        (client.update, sentinel.url, "apiclient.client.requests.patch"),
    ],
)
def test_data_parsing_delegates_to_request_formatter(client_method, url, patch_methodname):
    # GET and DELETE requests dont pass data so they are not being tested
    mock_request_formatter_call.reset_mock()

    with patch(patch_methodname) as mock_requests_method:
        requests_response = Mock(status_code=200)
        mock_requests_method.return_value = requests_response

        client_method(url, sentinel.data)

    mock_request_formatter_call.assert_called_once_with(sentinel.data)


def test_read_real_world_api(json_placeholder_cassette):
    client = JSONPlaceholderClient(
        authentication_method=NoAuthentication(),
        response_handler=JsonResponseHandler,
        request_formatter=JsonRequestFormatter,
    )
    assert len(client.get_all_todos()) == 200

    expected_todo = {
        "completed": False,
        "id": 45,
        "title": "velit soluta adipisci molestias reiciendis harum",
        "userId": 3,
    }
    assert client.get_todo(45) == expected_todo


@pytest.mark.parametrize(
    "status_code,expected_exception",
    [
        (HTTPStatus.MULTIPLE_CHOICES, exceptions.MultipleChoices),
        (HTTPStatus.MOVED_PERMANENTLY, exceptions.MovedPermanently),
        (HTTPStatus.FOUND, exceptions.Found),
        (HTTPStatus.SEE_OTHER, exceptions.SeeOther),
        (HTTPStatus.NOT_MODIFIED, exceptions.NotModified),
        (HTTPStatus.USE_PROXY, exceptions.UseProxy),
        (HTTPStatus.TEMPORARY_REDIRECT, exceptions.TemporaryRedirect),
        (HTTPStatus.PERMANENT_REDIRECT, exceptions.PermanentRedirect),
        (HTTPStatus.BAD_REQUEST, exceptions.BadRequest),
        (HTTPStatus.UNAUTHORIZED, exceptions.Unauthorized),
        (HTTPStatus.PAYMENT_REQUIRED, exceptions.PaymentRequired),
        (HTTPStatus.FORBIDDEN, exceptions.Forbidden),
        (HTTPStatus.NOT_FOUND, exceptions.NotFound),
        (HTTPStatus.NOT_ACCEPTABLE, exceptions.NotAcceptable),
        (HTTPStatus.PROXY_AUTHENTICATION_REQUIRED, exceptions.ProxyAuthenticationRequired),
        (HTTPStatus.REQUEST_TIMEOUT, exceptions.RequestTimeout),
        (HTTPStatus.CONFLICT, exceptions.Conflict),
        (HTTPStatus.GONE, exceptions.Gone),
        (HTTPStatus.LENGTH_REQUIRED, exceptions.LengthRequired),
        (HTTPStatus.PRECONDITION_FAILED, exceptions.PreconditionFailed),
        (HTTPStatus.REQUEST_ENTITY_TOO_LARGE, exceptions.RequestEntityTooLarge),
        (HTTPStatus.REQUEST_URI_TOO_LONG, exceptions.RequestUriTooLong),
        (HTTPStatus.UNSUPPORTED_MEDIA_TYPE, exceptions.UnsupportedMediaType),
        (HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE, exceptions.RequestedRangeNotSatisfiable),
        (HTTPStatus.EXPECTATION_FAILED, exceptions.ExpectationFailed),
        (HTTPStatus.UNPROCESSABLE_ENTITY, exceptions.UnprocessableEntity),
        (HTTPStatus.LOCKED, exceptions.Locked),
        (HTTPStatus.FAILED_DEPENDENCY, exceptions.FailedDependency),
        (HTTPStatus.UPGRADE_REQUIRED, exceptions.UpgradeRequired),
        (HTTPStatus.PRECONDITION_REQUIRED, exceptions.PreconditionRequired),
        (HTTPStatus.TOO_MANY_REQUESTS, exceptions.TooManyRequests),
        (HTTPStatus.REQUEST_HEADER_FIELDS_TOO_LARGE, exceptions.RequestHeaderFieldsTooLarge),
        (HTTPStatus.INTERNAL_SERVER_ERROR, exceptions.InternalServerError),
        (HTTPStatus.NOT_IMPLEMENTED, exceptions.NotImplemented),
        (HTTPStatus.BAD_GATEWAY, exceptions.BadGateway),
        (HTTPStatus.SERVICE_UNAVAILABLE, exceptions.ServiceUnavailable),
        (HTTPStatus.GATEWAY_TIMEOUT, exceptions.GatewayTimeout),
        (HTTPStatus.HTTP_VERSION_NOT_SUPPORTED, exceptions.HttpVersionNotSupported),
        (HTTPStatus.VARIANT_ALSO_NEGOTIATES, exceptions.VariantAlsoNegotiates),
        (HTTPStatus.INSUFFICIENT_STORAGE, exceptions.InsufficientStorage),
        (HTTPStatus.LOOP_DETECTED, exceptions.LoopDetected),
        (HTTPStatus.NOT_EXTENDED, exceptions.NotExtended),
        (HTTPStatus.NETWORK_AUTHENTICATION_REQUIRED, exceptions.NetworkAuthenticationRequired),
    ],
)
def test_exceptions_get_mapped_correctly_by_response_status_code(status_code, expected_exception):
    with patch("apiclient.client.requests.get") as mock_get:
        mock_get.return_value.status_code = status_code

        with pytest.raises(expected_exception):
            client.read(sentinel.url)
