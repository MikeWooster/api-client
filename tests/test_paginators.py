from unittest.mock import Mock

import pytest

from apiclient import APIClient, JsonRequestFormatter, JsonResponseHandler, paginated
from apiclient.authentication_methods import NoAuthentication
from apiclient.paginators import set_strategy
from apiclient.request_strategies import BaseRequestStrategy, RequestStrategy
from tests.helpers import client_factory


def next_page_param(response, previous_page_params):
    if response["next"]:
        return {"page": response["next"]}


def next_page_url(response, previous_page_url):
    if response["next"]:
        return response["next"]


class QueryPaginatedClient(APIClient):
    @paginated(by_query_params=next_page_param)
    def make_read_request(self):
        return self.get(endpoint="mock://testserver.com")


class UrlPaginatedClient(APIClient):
    @paginated(by_url=next_page_url)
    def make_read_request(self):
        return self.get(endpoint="mock://testserver.com")


def test_query_parameter_pagination(mock_requests):
    # Given the response is over three pages
    response_data = [
        {"page1": "data", "next": "page2"},
        {"page2": "data", "next": "page3"},
        {"page3": "data", "next": None},
    ]
    mock_requests.get(
        "mock://testserver.com",
        [
            {"json": {"page1": "data", "next": "page2"}, "status_code": 200},
            {"json": {"page2": "data", "next": "page3"}, "status_code": 200},
            {"json": {"page3": "data", "next": None}, "status_code": 200},
        ],
    )
    # mock_requests.get.side_effect = [build_response(json=page_data) for page_data in response_data]
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
    assert mock_requests.call_count == 3
    assert len(response) == 3
    assert response == response_data

    # And the clients paginator is reset back to the original.
    assert client.get_request_strategy() == original_strategy


def test_url_parameter_pagination(mock_requests):
    # Given the response is over two pages
    mock_requests.get(
        "mock://testserver.com",
        json={"page1": "data", "next": "mock://testserver.com/page2"},
        status_code=200,
    )
    mock_requests.get("mock://testserver.com/page2", json={"page2": "data", "next": None}, status_code=200)
    response_data = [
        {"page1": "data", "next": "mock://testserver.com/page2"},
        {"page2": "data", "next": None},
    ]
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
    assert mock_requests.call_count == 2
    assert response == response_data

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
