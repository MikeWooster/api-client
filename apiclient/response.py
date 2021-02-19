from typing import Any

import requests

from apiclient.utils.typing import JsonType


class Response:
    """
    Response abstracts away the underlying response, allowing
    us to pass around an interface representing the response
    without any need to knowledge of the underlying http
    implementation."""

    def get_original(self) -> Any:
        """Returns the original underlying response object."""
        raise NotImplementedError

    def get_status_code(self) -> int:
        """Returns the status code of the response."""
        raise NotImplementedError

    def get_raw_data(self) -> str:
        """Returns the content of the response, in unicode."""
        raise NotImplementedError

    def get_json(self) -> JsonType:
        """Returns the json-encoded content of a response."""
        raise NotImplementedError

    def get_status_reason(self) -> str:
        """Returns the textual representation of an HTTP status code, e.g. "NOT FOUND" or "OK"."""
        raise NotImplementedError

    def get_requested_url(self) -> str:
        """Returns the url to which the request was made."""
        raise NotImplementedError


class RequestsResponse(Response):
    """Implementation of the response for a requests.response type."""

    def __init__(self, response: requests.Response):
        self._response = response

    def get_original(self) -> Any:
        return self._response

    def get_status_code(self) -> int:
        return self._response.status_code

    def get_raw_data(self) -> str:
        return self._response.text

    def get_json(self) -> JsonType:
        return self._response.json()

    def get_status_reason(self) -> str:
        if not self._response.reason:
            return ""
        return self._response.reason

    def get_requested_url(self) -> str:
        return self._response.url
