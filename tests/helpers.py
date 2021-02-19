import json as json_lib
from io import BytesIO
from unittest.mock import Mock

import requests

from apiclient import APIClient, JsonRequestFormatter, JsonResponseHandler, NoAuthentication
from apiclient.request_formatters import BaseRequestFormatter
from apiclient.request_strategies import BaseRequestStrategy
from apiclient.response import RequestsResponse, Response
from apiclient.response_handlers import BaseResponseHandler

mock_response_handler_call = Mock()
mock_request_formatter_call = Mock()
mock_get_request_formatter_headers_call = Mock()


class MinimalClient(APIClient):
    """Minimal client - no implementation."""

    pass


class MockResponseHandler(BaseResponseHandler):
    """Mock class for testing."""

    @staticmethod
    def get_request_data(response):
        mock_response_handler_call(response)
        return response


class MockRequestFormatter(BaseRequestFormatter):
    """Mock class for testing."""

    @classmethod
    def get_headers(cls):
        mock_get_request_formatter_headers_call()
        return {}

    @classmethod
    def format(cls, data: dict):
        mock_request_formatter_call(data)
        return data


class NoOpRequestStrategy(BaseRequestStrategy):
    """Request strategy to mock out all calls below client."""

    def get(self, *args, **kwargs):
        pass

    def post(self, *args, **kwargs):
        pass

    def put(self, *args, **kwargs):
        pass

    def patch(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        pass


def build_response(data=None, json=None, status_code: int = 200) -> Response:
    """Builds a requests.Response object with the data set as the content."""
    response = requests.Response()
    response.status_code = status_code
    response.headers = {
        "Connection": "keep-alive",
        "Content-Encoding": "gzip",
        "Content-Type": "application/json; charset=utf-8",
    }
    response.encoding = "utf-8"
    if json:
        data = json_lib.dumps(json)
    response.raw = BytesIO(bytes(data, encoding="utf-8"))
    response.reason = "OK"
    response.url = "https://jsonplaceholder.typicode.com/todos"
    return RequestsResponse(response)


def client_factory(build_with=None, request_strategy=None):
    """Return an initialized client class."""
    factory_floor = {
        "json": MinimalClient(
            authentication_method=NoAuthentication(),
            response_handler=JsonResponseHandler,
            request_formatter=JsonRequestFormatter,
        ),
        "mocker": MinimalClient(
            authentication_method=NoAuthentication(),
            response_handler=MockResponseHandler,
            request_formatter=MockRequestFormatter,
        ),
    }
    client = factory_floor.get(build_with, factory_floor["mocker"])
    if request_strategy is not None:
        client.set_request_strategy(request_strategy)
    return client
