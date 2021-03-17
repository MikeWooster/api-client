from unittest.mock import Mock, sentinel

import pytest

from apiclient import NoAuthentication
from apiclient.client import APIClient
from apiclient.request_strategies import BaseRequestStrategy
from tests.helpers import MinimalClient, MockRequestFormatter, MockResponseHandler, client_factory


def test_client_initialization_with_invalid_authentication_method():
    assert 0
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


def test_client_initialization_with_invalid_exception_handler():
    with pytest.raises(RuntimeError) as exc_info:
        MinimalClient(
            authentication_method=NoAuthentication(),
            error_handler=None,
            request_formatter=MockRequestFormatter,
        )
    assert str(exc_info.value) == "provided error_handler must be a subclass of BaseErrorHandler."


def test_client_initialization_with_invalid_requests_handler():
    with pytest.raises(RuntimeError) as exc_info:
        MinimalClient(
            authentication_method=NoAuthentication(),
            response_handler=MockResponseHandler,
            request_formatter=None,
        )
    assert str(exc_info.value) == "provided request_formatter must be a subclass of BaseRequestFormatter."


def test_get_method_delegates_to_request_strategy():
    mock_request_strategy = Mock(spec=BaseRequestStrategy)
    mock_request_strategy.get.return_value = sentinel.response
    client = client_factory()
    client.set_request_strategy(mock_request_strategy)

    response = client.get(sentinel.url, params=sentinel.params, headers=sentinel.headers)

    mock_request_strategy.get.assert_called_once_with(
        sentinel.url, params=sentinel.params, headers=sentinel.headers
    )
    assert response == sentinel.response


def test_post_method_delegates_to_request_strategy():
    mock_request_strategy = Mock(spec=BaseRequestStrategy)
    mock_request_strategy.post.return_value = sentinel.response
    client = client_factory()
    client.set_request_strategy(mock_request_strategy)

    response = client.post(
        sentinel.url, data=sentinel.data, params=sentinel.params, headers=sentinel.headers
    )

    mock_request_strategy.post.assert_called_once_with(
        sentinel.url, data=sentinel.data, params=sentinel.params, headers=sentinel.headers
    )
    assert response == sentinel.response


def test_put_method_delegates_to_request_strategy():
    mock_request_strategy = Mock(spec=BaseRequestStrategy)
    mock_request_strategy.put.return_value = sentinel.response
    client = client_factory()
    client.set_request_strategy(mock_request_strategy)

    response = client.put(sentinel.url, data=sentinel.data, params=sentinel.params, headers=sentinel.headers)

    mock_request_strategy.put.assert_called_once_with(
        sentinel.url, data=sentinel.data, params=sentinel.params, headers=sentinel.headers
    )
    assert response == sentinel.response


def test_patch_method_delegates_to_request_strategy():
    mock_request_strategy = Mock(spec=BaseRequestStrategy)
    mock_request_strategy.patch.return_value = sentinel.response
    client = client_factory()
    client.set_request_strategy(mock_request_strategy)

    response = client.patch(
        sentinel.url, data=sentinel.data, params=sentinel.params, headers=sentinel.headers
    )

    mock_request_strategy.patch.assert_called_once_with(
        sentinel.url, data=sentinel.data, params=sentinel.params, headers=sentinel.headers
    )
    assert response == sentinel.response


def test_delete_method_delegates_to_request_strategy():
    mock_request_strategy = Mock(spec=BaseRequestStrategy)
    mock_request_strategy.delete.return_value = sentinel.response
    client = client_factory()
    client.set_request_strategy(mock_request_strategy)

    response = client.delete(sentinel.url, params=sentinel.params, headers=sentinel.headers)

    mock_request_strategy.delete.assert_called_once_with(
        sentinel.url, params=sentinel.params, headers=sentinel.headers
    )
    assert response == sentinel.response


def test_setting_incorrect_request_strategy_raises_runtime_error():
    client = client_factory()
    with pytest.raises(RuntimeError) as exc_info:
        client.set_request_strategy("not a strategy")
    assert str(exc_info.value) == "provided request_strategy must be an instance of BaseRequestStrategy."


def test_client_get_and_set_session():
    client = APIClient()
    client.set_session(sentinel.session)
    assert client.get_session() == sentinel.session


def test_client_clone_method():
    client = client_factory(build_with="json")
    client.set_session(sentinel.session)
    new_client = client.clone()
    assert new_client.get_session() is client.get_session()
