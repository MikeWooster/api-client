from unittest.mock import Mock, sentinel

from apiclient.request_strategies import (
    BaseRequestStrategy,
    QueryParamPaginatedRequestStrategy,
    UrlPaginatedRequestStrategy,
)
from tests.helpers import build_response, client_factory


def request_strategy_factory(strategy_class, next_page):
    client = client_factory(build_with="json")
    strategy = strategy_class(next_page)
    strategy.set_client(client)
    return strategy


def test_setting_and_getting_client():
    strategy = BaseRequestStrategy()
    strategy.set_client(sentinel.client)
    assert strategy.get_client() == sentinel.client


def test_query_param_paginated_strategy_delegates_to_callable(mock_requests):
    # Given our next page callable will return a None value
    next_page = Mock(return_value=None)

    mock_requests.get.return_value = build_response(json={"foo": "bar"})

    strategy = request_strategy_factory(QueryParamPaginatedRequestStrategy, next_page)

    # When we request the page
    response = strategy.get("http://example.com")

    # Then the first page is fetched and the paginator stops
    assert list(response) == [{"foo": "bar"}]
    assert mock_requests.get.call_count == 1
    # And the paginator is called with the latest response and the original params
    next_page.assert_called_once_with({"foo": "bar"}, {})


def test_url_paginated_strategy_delegates_to_callable(mock_requests):
    # Given our next page callable will return a None value
    next_page = Mock(return_value=None)

    mock_requests.get.return_value = build_response(json={"foo": "bar"})

    strategy = request_strategy_factory(UrlPaginatedRequestStrategy, next_page)

    # When we request the page
    response = strategy.get("http://example.com")

    # Then the first page is fetched and the paginator stops
    assert list(response) == [{"foo": "bar"}]
    assert mock_requests.get.call_count == 1
    next_page.assert_called_once_with({"foo": "bar"}, "http://example.com")
