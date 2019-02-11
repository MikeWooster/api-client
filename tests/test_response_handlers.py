import json
from io import BytesIO
from unittest.mock import sentinel

import pytest
from requests import Response

from api_client.exceptions import ClientUnexpectedError
from api_client.response_handlers import RequestsResponseHandler, JsonResponseHandler, BaseResponseHandler


def build_response(data) -> Response:
    """Return a requests.Response object with the data set as the content."""
    response = Response()
    response.status_code = 200
    response.headers = {
        'Connection': 'keep-alive',
        'Content-Encoding': 'gzip',
        'Content-Type': 'application/json; charset=utf-8',
    }
    response.encoding = 'utf-8'
    response.raw = BytesIO(bytes(data, encoding='utf-8'))
    response.reason = "OK"
    response.url = 'https://jsonplaceholder.typicode.com/todos'
    return response


class TestBaseResponseHandler:
    handler = BaseResponseHandler

    def test_get_request_data_needs_implementation(self):
        with pytest.raises(NotImplementedError):
            self.handler.get_request_data(sentinel.response)


class TestRequestsResponseHandler:
    handler = RequestsResponseHandler

    def test_original_response_is_returned(self):
        data = self.handler.get_request_data(sentinel.response)
        assert data == sentinel.response


class TestJsonResponseHandler:
    handler = JsonResponseHandler

    def test_response_json_is_parsed_correctly(self):
        response = build_response(data=json.dumps({"foo": "bar"}))
        data = self.handler.get_request_data(response)
        assert data == {"foo": "bar"}

    def test_bad_json_raises_unexpected_error(self):
        response = build_response(data="foo")
        with pytest.raises(ClientUnexpectedError) as exc_info:
            self.handler.get_request_data(response)
        assert str(exc_info.value) == "Unable to decode response data to json. data='foo'"