from unittest.mock import Mock

import pytest

from apiclient.response import AioHttpResponse, RequestsResponse, Response


class TestResponse:
    """Simple tests for 100% coverage - testing abstract class."""

    response = Response()

    @pytest.mark.parametrize(
        "method",
        [
            response.get_original,
            response.get_status_code,
            response.get_raw_data,
            response.get_json,
            response.get_status_reason,
            response.get_requested_url,
        ],
    )
    def test_needs_implementation(self, method):
        with pytest.raises(NotImplementedError):
            method()


class TestRequestsResponse:
    def test_get_status_reason_returns_empty_string_when_none(self):
        requests_response = Mock(reason=None)
        response = RequestsResponse(requests_response)
        assert response.get_status_reason() == ""


class TestAiRequestsResponse:
    def test_get_url(self):
        requests_response = Mock(url=1)
        response = AioHttpResponse(requests_response, b"")
        assert response.get_requested_url() == "1"
