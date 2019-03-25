import logging
from unittest.mock import Mock, patch, sentinel

import pytest

from apiclient.authentication_methods import BaseAuthenticationMethod, NoAuthentication
from apiclient.client import LOG as client_logger
from apiclient.client import BaseClient
from apiclient.exceptions import ClientError, RedirectionError, ServerError, UnexpectedError
from apiclient.request_formatters import JsonRequestFormatter
from apiclient.response_handlers import JsonResponseHandler
from tests.helpers import (
    MinimalClient,
    MockRequestFormatter,
    MockResponseHandler,
    client_factory,
    mock_get_request_formatter_headers_call,
    mock_request_formatter_call,
    mock_response_handler_call,
)


# Real world api client with GET methods implemented.
class JSONPlaceholderClient(BaseClient):
    base_url = "https://jsonplaceholder.typicode.com"

    def get_all_todos(self) -> dict:
        url = f"{self.base_url}/todos"
        return self.read(url)

    def get_todo(self, todo_id: int) -> dict:
        url = f"{self.base_url}/todos/{todo_id}"
        return self.read(url)


def test_client_initialization_with_invalid_authentication_method():
    with pytest.raises(RuntimeError) as exc_info:
        MinimalClient(
            authentication_method=None,
            response_handler=MockResponseHandler,
            request_formatter=MockRequestFormatter,
        )
    expected_message = "provided authentication_method must be an instance of BaseAuthenticationMethod."
    assert str(exc_info.value) == expected_message


def test_client_initialization_with_invalid_response_handler():
    with pytest.raises(RuntimeError) as exc_info:
        MinimalClient(
            authentication_method=NoAuthentication(),
            response_handler=None,
            request_formatter=MockRequestFormatter,
        )
    assert str(exc_info.value) == "provided response_handler must be a subclass of BaseResponseHandler."


def test_client_initialization_with_invalid_requests_handler():
    with pytest.raises(RuntimeError) as exc_info:
        MinimalClient(
            authentication_method=NoAuthentication(),
            response_handler=MockResponseHandler,
            request_formatter=None,
        )
    assert str(exc_info.value) == "provided request_formatter must be a subclass of BaseRequestFormatter."


@patch("apiclient.request_strategies.requests")
def test_create_method_success(mock_requests):
    mock_requests.post.return_value.status_code = 201
    client_factory().create(sentinel.url, data={"foo": "bar"})
    mock_requests.post.assert_called_once_with(
        sentinel.url, auth=None, headers={}, data={"foo": "bar"}, params={}, timeout=10.0
    )


@patch("apiclient.request_strategies.requests")
def test_create_method_with_params(mock_requests):
    mock_requests.post.return_value.status_code = 201
    client_factory().create(sentinel.url, data={"foo": "bar"}, params={"query": "foo"})
    mock_requests.post.assert_called_once_with(
        sentinel.url, auth=None, headers={}, data={"foo": "bar"}, params={"query": "foo"}, timeout=10.0
    )


@patch("apiclient.request_strategies.requests")
def test_read_method_success(mock_requests):
    mock_requests.get.return_value.status_code = 200
    client_factory().read(sentinel.url)
    mock_requests.get.assert_called_once_with(
        sentinel.url, auth=None, headers={}, params={}, data=None, timeout=10.0
    )


@patch("apiclient.request_strategies.requests")
def test_replace_method_success(mock_requests):
    mock_requests.put.return_value.status_code = 200
    client_factory().replace(sentinel.url, data={"foo": "bar"})
    mock_requests.put.assert_called_once_with(
        sentinel.url, auth=None, headers={}, data={"foo": "bar"}, params={}, timeout=10.0
    )


@patch("apiclient.request_strategies.requests")
def test_update_method_success(mock_requests):
    mock_requests.patch.return_value.status_code = 200
    client_factory().update(sentinel.url, data={"foo": "bar"})
    mock_requests.patch.assert_called_once_with(
        sentinel.url, auth=None, headers={}, data={"foo": "bar"}, params={}, timeout=10.0
    )


@patch("apiclient.request_strategies.requests")
def test_delete_method_success(mock_requests):
    mock_requests.delete.return_value.status_code = 200
    client_factory().delete(sentinel.url)
    mock_requests.delete.assert_called_once_with(
        sentinel.url, auth=None, headers={}, params={}, data=None, timeout=10.0
    )


@patch("apiclient.request_strategies.requests")
def test_authentication_methods_are_called(mock_requests):
    mock_requests.get.return_value.status_code = 200
    mock_authentication = Mock(spec=BaseAuthenticationMethod)
    mock_authentication.get_headers.return_value = {sentinel.key: sentinel.value}
    mock_authentication.get_query_params.return_value = {sentinel.pkey: sentinel.pvalue}
    mock_authentication.get_username_password_authentication.return_value = (sentinel.uname, sentinel.pwd)

    client = MinimalClient(
        authentication_method=mock_authentication,
        response_handler=MockResponseHandler,
        request_formatter=MockRequestFormatter,
    )
    client.read(sentinel.url)

    mock_requests.get.assert_called_once_with(
        sentinel.url,
        auth=(sentinel.uname, sentinel.pwd),
        headers={sentinel.key: sentinel.value},
        params={sentinel.pkey: sentinel.pvalue},
        data=None,
        timeout=10.0,
    )
    assert mock_authentication.get_headers.call_count == 1
    assert mock_authentication.get_query_params.call_count == 1
    assert mock_authentication.get_username_password_authentication.call_count == 1


@patch("apiclient.request_strategies.requests")
def test_request_formatter_methods_are_called(mock_requests):
    mock_get_request_formatter_headers_call.reset_mock()
    mock_requests.get.return_value.status_code = 200

    client = MinimalClient(
        authentication_method=NoAuthentication(),
        response_handler=MockResponseHandler,
        request_formatter=MockRequestFormatter,
    )
    client.read(sentinel.url)

    mock_requests.get.assert_called_once_with(
        sentinel.url, auth=None, headers={}, params={}, data=None, timeout=10.0
    )
    assert mock_get_request_formatter_headers_call.call_count == 1


@pytest.mark.parametrize(
    "client_method,client_args,patch_methodname",
    [
        (
            client_factory().create,
            (sentinel.url, {"foo": "bar"}),
            "apiclient.request_strategies.requests.post",
        ),
        (client_factory().read, (sentinel.url,), "apiclient.request_strategies.requests.get"),
        (
            client_factory().replace,
            (sentinel.url, {"foo": "bar"}),
            "apiclient.request_strategies.requests.put",
        ),
        (
            client_factory().update,
            (sentinel.url, {"foo": "bar"}),
            "apiclient.request_strategies.requests.patch",
        ),
        (client_factory().delete, (sentinel.url,), "apiclient.request_strategies.requests.delete"),
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
        (
            client_factory().create,
            (sentinel.url, {"foo": "bar"}),
            "apiclient.request_strategies.requests.post",
        ),
        (client_factory().read, (sentinel.url,), "apiclient.request_strategies.requests.get"),
        (
            client_factory().replace,
            (sentinel.url, {"foo": "bar"}),
            "apiclient.request_strategies.requests.put",
        ),
        (
            client_factory().update,
            (sentinel.url, {"foo": "bar"}),
            "apiclient.request_strategies.requests.patch",
        ),
        (client_factory().delete, (sentinel.url,), "apiclient.request_strategies.requests.delete"),
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
        (
            client_factory().create,
            (sentinel.url, {"foo": "bar"}),
            "apiclient.request_strategies.requests.post",
        ),
        (client_factory().read, (sentinel.url,), "apiclient.request_strategies.requests.get"),
        (
            client_factory().replace,
            (sentinel.url, {"foo": "bar"}),
            "apiclient.request_strategies.requests.put",
        ),
        (
            client_factory().update,
            (sentinel.url, {"foo": "bar"}),
            "apiclient.request_strategies.requests.patch",
        ),
        (client_factory().delete, (sentinel.url,), "apiclient.request_strategies.requests.delete"),
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
        (
            client_factory().create,
            (sentinel.url, {"foo": "bar"}),
            "apiclient.request_strategies.requests.post",
        ),
        (client_factory().read, (sentinel.url,), "apiclient.request_strategies.requests.get"),
        (
            client_factory().replace,
            (sentinel.url, {"foo": "bar"}),
            "apiclient.request_strategies.requests.put",
        ),
        (
            client_factory().update,
            (sentinel.url, {"foo": "bar"}),
            "apiclient.request_strategies.requests.patch",
        ),
        (client_factory().delete, (sentinel.url,), "apiclient.request_strategies.requests.delete"),
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
        (
            client_factory().create,
            (sentinel.url, {"foo": "bar"}),
            "apiclient.request_strategies.requests.post",
        ),
        (client_factory().read, (sentinel.url,), "apiclient.request_strategies.requests.get"),
        (
            client_factory().replace,
            (sentinel.url, {"foo": "bar"}),
            "apiclient.request_strategies.requests.put",
        ),
        (
            client_factory().update,
            (sentinel.url, {"foo": "bar"}),
            "apiclient.request_strategies.requests.patch",
        ),
        (client_factory().delete, (sentinel.url,), "apiclient.request_strategies.requests.delete"),
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
        (client_factory().read, (sentinel.url,), "apiclient.request_strategies.requests.get"),
        (
            client_factory().replace,
            (sentinel.url, {"foo": "bar"}),
            "apiclient.request_strategies.requests.put",
        ),
        (
            client_factory().update,
            (sentinel.url, {"foo": "bar"}),
            "apiclient.request_strategies.requests.patch",
        ),
        (client_factory().delete, (sentinel.url,), "apiclient.request_strategies.requests.delete"),
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
        (
            client_factory().create,
            (sentinel.url, {"foo": "bar"}),
            "apiclient.request_strategies.requests.post",
        ),
        (client_factory().read, (sentinel.url,), "apiclient.request_strategies.requests.get"),
        (
            client_factory().replace,
            (sentinel.url, {"foo": "bar"}),
            "apiclient.request_strategies.requests.put",
        ),
        (
            client_factory().update,
            (sentinel.url, {"foo": "bar"}),
            "apiclient.request_strategies.requests.patch",
        ),
        (client_factory().delete, (sentinel.url,), "apiclient.request_strategies.requests.delete"),
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
        (client_factory().create, sentinel.url, "apiclient.request_strategies.requests.post"),
        (client_factory().replace, sentinel.url, "apiclient.request_strategies.requests.put"),
        (client_factory().update, sentinel.url, "apiclient.request_strategies.requests.patch"),
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


def test_setting_incorrect_request_strategy_raises_runtime_error():
    client = client_factory()
    with pytest.raises(RuntimeError) as exc_info:
        client.set_request_strategy("not a strategy")
    assert str(exc_info.value) == "provided request_strategy must be an instance of BaseRequestStrategy."
