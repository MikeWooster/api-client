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
    next_page = Mock(side_effect=ValueError("something went wrong"))

    # When the response does not return the next page parameter.
    mock_requests.get.return_value = build_response(json={"foo": "bar"})

    strategy = request_strategy_factory(QueryParamPaginatedRequestStrategy, next_page)

    response = strategy.read("http://example.com")

    assert list(response) == [{"foo": "bar"}]
    assert mock_requests.get.call_count == 1
    next_page.assert_called_once_with({"foo": "bar"})


def test_query_param_paginated_strategy_stops_paginating_when_encounters_error(mock_requests):
    def next_page(response):
        raise ValueError("something went wrong")

    # When the response does not return the next page parameter.
    mock_requests.get.return_value = build_response(json={"foo": "bar"})

    strategy = request_strategy_factory(QueryParamPaginatedRequestStrategy, next_page)

    response = strategy.read("http://example.com")

    assert list(response) == [{"foo": "bar"}]
    assert mock_requests.get.call_count == 1


def test_url_paginated_strategy_delegates_to_callable(mock_requests):
    next_page = Mock(side_effect=ValueError("something went wrong"))

    # When the response does not return the next page parameter.
    mock_requests.get.return_value = build_response(json={"foo": "bar"})

    strategy = request_strategy_factory(UrlPaginatedRequestStrategy, next_page)

    response = strategy.read("http://example.com")

    assert list(response) == [{"foo": "bar"}]
    assert mock_requests.get.call_count == 1
    next_page.assert_called_once_with({"foo": "bar"})


def test_url_paginated_strategy_stops_paginating_when_encounters_error(mock_requests):
    def next_page(response):
        raise ValueError("something went wrong")

    # When the response does not return the next page parameter.
    mock_requests.get.return_value = build_response(json={"foo": "bar"})

    strategy = request_strategy_factory(UrlPaginatedRequestStrategy, next_page)

    response = strategy.read("http://example.com")

    assert list(response) == [{"foo": "bar"}]
    assert mock_requests.get.call_count == 1
