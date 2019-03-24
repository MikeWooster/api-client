import json as json_lib
from io import BytesIO
from unittest.mock import Mock

from requests import Response

from apiclient import BaseClient
from apiclient.authentication_methods import NoAuthentication
from apiclient.request_formatters import BaseRequestFormatter, JsonRequestFormatter
from apiclient.response_handlers import BaseResponseHandler, JsonResponseHandler

mock_response_handler_call = Mock()
mock_request_formatter_call = Mock()


class MinimalClient(BaseClient):
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
    def format(cls, data: dict):
        mock_request_formatter_call(data)
        return data


def build_response(data=None, json=None) -> Response:
    """Return a requests.Response object with the data set as the content."""
    response = Response()
    response.status_code = 200
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
    return response


def client_factory(build_with=None):
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
    return factory_floor.get(build_with, factory_floor["mocker"])
