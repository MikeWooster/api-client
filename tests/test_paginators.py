from unittest.mock import Mock, call

import pytest

from apiclient import APIClient, JsonRequestFormatter, JsonResponseHandler, paginated
from apiclient.authentication_methods import NoAuthentication
from apiclient.paginators import set_strategy
from apiclient.request_strategies import BaseRequestStrategy, RequestStrategy
from tests.helpers import build_response, client_factory


def next_page_param(response):
    if response["next"]:
        return {"page": response["next"]}


def next_page_url(response):
    if response["next"]:
        return response["next"]


class QueryPaginatedClient(APIClient):
    @paginated(by_query_params=next_page_param)
    def make_read_request(self):
        return self.get(endpoint="http://example.com")


class UrlPaginatedClient(APIClient):
    @paginated(by_url=next_page_url)
    def make_read_request(self):
        return self.get(endpoint="http://example.com")


def test_query_parameter_pagination(mock_requests):
    # Given the response is over two pages
    response_data = [{"page1": "data", "next": "page2"}, {"page2": "data", "next": None}]
    mock_requests.get.side_effect = [build_response(json=page_data) for page_data in response_data]
    client = QueryPaginatedClient(
        authentication_method=NoAuthentication(),
        response_handler=JsonResponseHandler,
        request_formatter=JsonRequestFormatter,
    )
    # And the client has been set up with the SinglePagePaginator
    original_strategy = client.get_request_strategy()
    assert isinstance(original_strategy, RequestStrategy)

    # When I call the client method
    response = list(client.make_read_request())

    # Then two requests are made to get both pages
    assert mock_requests.get.call_count == 2
    assert len(response) == 2
    assert response == response_data
    defaults = {"auth": None, "data": None, "headers": {"Content-type": "application/json"}, "timeout": 10}
    expected_call_args = [
        call("http://example.com", params={}, **defaults),
        call("http://example.com", params={"page": "page2"}, **defaults),
    ]
    assert mock_requests.get.call_args_list == expected_call_args

    # And the clients paginator is reset back to the original.
    assert client.get_request_strategy() == original_strategy


def test_url_parameter_pagination(mock_requests):
    # Given the response is over two pages
    response_data = [{"page1": "data", "next": "http://example.com/page2"}, {"page2": "data", "next": None}]
    mock_requests.get.side_effect = [build_response(json=page_data) for page_data in response_data]
    client = UrlPaginatedClient(
        authentication_method=NoAuthentication(),
        response_handler=JsonResponseHandler,
        request_formatter=JsonRequestFormatter,
    )
    # And the client has been set up with the SinglePagePaginator
    original_strategy = client.get_request_strategy()
    assert isinstance(original_strategy, RequestStrategy)

    # When I call the client method
    response = list(client.make_read_request())

    # Then two requests are made to get both pages
    assert mock_requests.get.call_count == 2
    assert response == response_data
    defaults = {
        "auth": None,
        "data": None,
        "headers": {"Content-type": "application/json"},
        "params": {},
        "timeout": 10,
    }
    expected_call_args = [
        call("http://example.com", **defaults),
        call("http://example.com/page2", **defaults),
    ]
    assert mock_requests.get.call_args_list == expected_call_args

    # And the clients paginator is reset back to the original.
    assert client.get_request_strategy() == original_strategy


def test_set_strategy_changes_strategy_on_copy_of_client_when_in_context():
    client = client_factory()
    original_strategy = client.get_request_strategy()
    new_strategy = Mock(spec=BaseRequestStrategy)

    with set_strategy(client, new_strategy) as temporary_client:
        assert client.get_request_strategy() == original_strategy
        assert temporary_client.get_request_strategy() == new_strategy

    assert client.get_request_strategy() == original_strategy


def test_context_manager_resets_request_strategy_when_error():
    client = client_factory()
    original_strategy = client.get_request_strategy()
    new_strategy = Mock(spec=BaseRequestStrategy)
    raises_when_called = Mock(side_effect=ValueError("Something went wrong"))

    with pytest.raises(ValueError):
        with set_strategy(client, new_strategy):
            raises_when_called()

    assert client.get_request_strategy() == original_strategy
