from unittest.mock import Mock, call, sentinel

import aiohttp
import pytest

from apiclient import APIClient
from apiclient.client import AsyncClient
from apiclient.request_strategies import (
    AsyncRequestStrategy,
    BaseRequestStrategy,
    QueryParamPaginatedRequestStrategy,
    RequestStrategy,
    UrlPaginatedRequestStrategy,
)
from tests.helpers import client_factory


def request_strategy_factory(strategy_class, build_client_with="json", **kwargs):
    """Helper method to build a strategy with a client."""
    client = client_factory(build_with=build_client_with)
    strategy = strategy_class(**kwargs)
    strategy.set_client(client)
    return strategy


def test_setting_and_getting_client():
    strategy = BaseRequestStrategy()
    strategy.set_client(sentinel.client)
    assert strategy.get_client() == sentinel.client


def assert_request_called_once(mock_requests, expected_url, expected_method):
    assert mock_requests.call_count == 1
    history = mock_requests.request_history
    assert history[0].url == expected_url
    assert history[0].method == expected_method


def assert_mock_client_called_once(mock_client, expected_request_data):
    assert mock_client.client.get_default_query_params.call_count == 1
    assert mock_client.client.get_default_headers.call_count == 1
    assert mock_client.client.get_default_username_password_authentication.call_count == 1
    assert mock_client.request_formatter.format.call_count == 1
    assert mock_client.request_formatter.format.call_args == call(expected_request_data)
    assert mock_client.client.get_request_timeout.call_count == 1


def test_request_strategy_sets_session_on_parent_when_not_already_set(mock_client):
    mock_client.client.get_session.return_value = None
    strategy = RequestStrategy()
    strategy.set_client(mock_client.client)
    mock_client.client.get_session.assert_called_once_with()
    mock_client.client.set_session.assert_called_once()


def test_request_strategy_does_not_set_session_if_already_set(mock_client):
    mock_client.client.get_session.return_value = sentinel.session
    strategy = RequestStrategy()
    strategy.set_client(mock_client.client)
    mock_client.client.get_session.assert_called_once_with()
    mock_client.client.set_session.assert_not_called()


def test_request_strategy_get_method_delegates_to_parent_handlers(mock_requests, mock_client):
    mock_requests.get("mock://testserver.com", json={"active": True}, status_code=200)

    strategy = RequestStrategy()
    strategy.set_client(mock_client.client)

    response = strategy.get("mock://testserver.com", params={"foo": sentinel.params})

    assert response == sentinel.result
    assert_request_called_once(mock_requests, "mock://testserver.com", "GET")
    assert_mock_client_called_once(mock_client, None)


def test_request_strategy_post_method_delegates_to_parent_handlers(mock_requests, mock_client):
    mock_requests.post("mock://testserver.com", json={"active": True}, status_code=200)

    strategy = RequestStrategy()
    strategy.set_client(mock_client.client)

    response = strategy.post(
        "mock://testserver.com", data={"data": sentinel.data}, params={"foo": sentinel.params}
    )

    assert response == sentinel.result
    assert_request_called_once(mock_requests, "mock://testserver.com", "POST")
    assert_mock_client_called_once(mock_client, {"data": sentinel.data})


def test_request_strategy_put_method_delegates_to_parent_handlers(mock_requests, mock_client):
    mock_requests.put("mock://testserver.com", json={"active": True}, status_code=200)

    strategy = RequestStrategy()
    strategy.set_client(mock_client.client)

    response = strategy.put(
        "mock://testserver.com", data={"data": sentinel.data}, params={"foo": sentinel.params}
    )

    assert response == sentinel.result
    assert_request_called_once(mock_requests, "mock://testserver.com", "PUT")
    assert_mock_client_called_once(mock_client, {"data": sentinel.data})


def test_request_strategy_patch_method_delegates_to_parent_handlers(mock_requests, mock_client):
    mock_requests.patch("mock://testserver.com", json={"active": True}, status_code=200)

    strategy = RequestStrategy()
    strategy.set_client(mock_client.client)

    response = strategy.patch(
        "mock://testserver.com", data={"data": sentinel.data}, params={"foo": sentinel.params}
    )

    assert response == sentinel.result
    assert_request_called_once(mock_requests, "mock://testserver.com", "PATCH")
    assert_mock_client_called_once(mock_client, {"data": sentinel.data})


def test_request_strategy_delete_method_delegates_to_parent_handlers(mock_requests, mock_client):
    mock_requests.delete("mock://testserver.com", json={"active": True}, status_code=200)

    strategy = RequestStrategy()
    strategy.set_client(mock_client.client)

    response = strategy.delete("mock://testserver.com", params={"foo": sentinel.params})

    assert response == sentinel.result
    assert_request_called_once(mock_requests, "mock://testserver.com", "DELETE")
    assert_mock_client_called_once(mock_client, None)


@pytest.mark.parametrize("initial_params", [{"my-param": "always-set"}, None])
def test_query_param_paginated_strategy_delegates_to_callable(initial_params, mock_requests):
    # Given our next page callable will return:
    # - a page 2 param
    # - a None value - indicating it is the final page
    mock_requests.get(
        "mock://testserver.com",
        [
            {"json": {"data": ["element1", "element2"], "nextPage": "2"}, "status_code": 200},
            {"json": {"data": ["element3", "element4"], "nextPage": None}, "status_code": 200},
        ],
    )

    def next_page_callback(response, previous_params):
        return {"nextPage": response["nextPage"]} if response["nextPage"] else None

    strategy = request_strategy_factory(QueryParamPaginatedRequestStrategy, next_page=next_page_callback)

    # When we request the page
    response = strategy.get("mock://testserver.com", params=initial_params)

    # Then the first page is fetched and the paginator stops
    assert list(response) == [
        {"data": ["element1", "element2"], "nextPage": "2"},
        {"data": ["element3", "element4"], "nextPage": None},
    ]
    assert mock_requests.called
    assert mock_requests.call_count == 2
    history = mock_requests.request_history
    assert history[0].url == "mock://testserver.com"
    assert history[1].url == "mock://testserver.com"


def test_url_paginated_strategy_delegates_to_callable(mock_requests):
    # Given our next page callable will return:
    # - first, a new url for the request to go to.
    # - second, a none value telling the paginator to stop.
    mock_requests.get(
        "mock://testserver.com",
        json={"data": ["element1", "element2"], "nextPage": "mock://testserver.com/2"},
        status_code=200,
    )
    mock_requests.get(
        "mock://testserver.com/2", json={"data": ["element3", "element4"], "nextPage": None}, status_code=200
    )

    def next_page_callback(response, previous_params):
        return response["nextPage"]

    strategy = request_strategy_factory(UrlPaginatedRequestStrategy, next_page=next_page_callback)

    # When we request the page
    response = strategy.get("mock://testserver.com")

    # Then the first page is fetched and the paginator stops
    assert list(response) == [
        {"data": ["element1", "element2"], "nextPage": "mock://testserver.com/2"},
        {"data": ["element3", "element4"], "nextPage": None},
    ]
    assert mock_requests.called
    assert mock_requests.call_count == 2
    # And the paginator is called with the latest response and the original params
    history = mock_requests.request_history
    assert history[0].url == "mock://testserver.com"
    assert history[1].url == "mock://testserver.com/2"


class MyClient(APIClient):
    async def get_stuff(self):
        resp = self.get("https://example.com")
        return await resp


@pytest.mark.asyncio
async def test_async_get():
    # async def fetch(session, url):
    #     async with session.get(url) as response:
    #         return await response.text()
    #
    # async def main():
    #     session = aiohttp.ClientSession()
    #
    #     html = await fetch(session, "http://python.org")
    #     print(html)
    #
    # assert await main() == "foo"
    async with AsyncClient() as client:
        assert await client.get("http://example.com") == "foo"
