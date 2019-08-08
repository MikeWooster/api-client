from unittest.mock import Mock, call, sentinel

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
    # Given our next page callable will return:
    # - a page 2 param
    # - a None value - indicating the end of the requests
    next_page = Mock(side_effect=({"my-next-page": 2}, None))

    # The first time we hit the page, we get told that next page is 2
    # The second time, we will get told that there is no next page
    mock_requests.get.side_effect = (
        build_response(json={"data": ["element1", "element2"], "nextPage": "2"}),
        build_response(json={"data": ["element3", "element4"], "nextPage": None}),
    )

    strategy = request_strategy_factory(QueryParamPaginatedRequestStrategy, next_page)

    # When we request the page
    response = strategy.get("http://example.com", params={"my-param": "always-set"})

    # Then the first page is fetched and the paginator stops
    assert list(response) == [
        {"data": ["element1", "element2"], "nextPage": "2"},
        {"data": ["element3", "element4"], "nextPage": None},
    ]
    assert mock_requests.get.call_count == 2

    # And the paginator is called with the latest response and the original params
    expected_calls = [
        # The first call should be called with the first response and the original params.
        call({"data": ["element1", "element2"], "nextPage": "2"}, {"my-param": "always-set"}),
        # The second call should be called with the second response and the original param
        # plus the next page param added to the params dict from the first next page call.
        call(
            {"data": ["element3", "element4"], "nextPage": None},
            {"my-param": "always-set", "my-next-page": 2},
        ),
    ]
    assert next_page.call_args_list == expected_calls


def test_url_paginated_strategy_delegates_to_callable(mock_requests):
    # Given our next page callable will return:
    # - first, a new url for the request to go to.
    # - second, a none value telling the paginator to stop.
    next_page = Mock(side_effect=("http://example.com/2", None))

    mock_requests.get.side_effect = (
        build_response(json={"data": ["element1", "element2"], "nextPage": "http://example.com/2"}),
        build_response(json={"data": ["element3", "element4"], "nextPage": None}),
    )

    strategy = request_strategy_factory(UrlPaginatedRequestStrategy, next_page)

    # When we request the page
    response = strategy.get("http://example.com")

    # Then the first page is fetched and the paginator stops
    assert list(response) == [
        {"data": ["element1", "element2"], "nextPage": "http://example.com/2"},
        {"data": ["element3", "element4"], "nextPage": None},
    ]
    assert mock_requests.get.call_count == 2
    # And the paginator is called with the latest response and the original params

    expected_calls = [
        # The first call should be called with the first response and the original url.
        call({"data": ["element1", "element2"], "nextPage": "http://example.com/2"}, "http://example.com"),
        # The second call should be called with the second response and the second page url
        call({"data": ["element3", "element4"], "nextPage": None}, "http://example.com/2"),
    ]
    assert next_page.call_args_list == expected_calls
