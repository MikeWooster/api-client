import logging
from typing import Callable, Type

import requests
from requests import Response

from apiclient import exceptions
from apiclient.interface import IClient
from apiclient.utils.typing import OptionalDict

LOG = logging.getLogger(__name__)


class BaseRequestStrategy:
    def set_client(self, client: IClient):
        self._client = client

    def get_client(self) -> IClient:
        return self._client

    def create(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def read(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def replace(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def update(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def delete(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError


class RequestStrategy(BaseRequestStrategy):
    def create(self, endpoint: str, data: dict, params: OptionalDict = None):
        """Send data and return response data from POST endpoint."""
        return self._make_request(requests.post, endpoint, data=data, params=params)

    def read(self, endpoint: str, params: OptionalDict = None):
        """Return response data from GET endpoint."""
        return self._make_request(requests.get, endpoint, params=params)

    def replace(self, endpoint: str, data: dict, params: OptionalDict = None):
        """Send data to overwrite resource and return response data from PUT endpoint."""
        return self._make_request(requests.put, endpoint, data=data, params=params)

    def update(self, endpoint: str, data: dict, params: OptionalDict = None):
        """Send data to update resource and return response data from PATCH endpoint."""
        return self._make_request(requests.patch, endpoint, data=data, params=params)

    def delete(self, endpoint: str, params: OptionalDict = None):
        """Remove resource with DELETE endpoint."""
        return self._make_request(requests.delete, endpoint, params=params)

    def _make_request(
        self,
        request_method: Callable,
        endpoint: str,
        params: OptionalDict = None,
        headers: OptionalDict = None,
        data: OptionalDict = None,
        **kwargs,
    ) -> Response:
        """Make the request with the given method.

        Delegates response parsing to the response handler.
        """
        try:
            response = request_method(
                endpoint,
                params=self._get_request_params(params),
                headers=self._get_request_headers(headers),
                auth=self._get_username_password_authentication(),
                data=self._get_formatted_data(data),
                timeout=self._get_request_timeout(),
                **kwargs,
            )
        except Exception as error:
            LOG.error(f"An error occurred when contacting %s", endpoint, exc_info=error)
            raise exceptions.UnexpectedError(f"Error when contacting '{endpoint}'") from error
        else:
            self._check_response(response)
        return self._decode_response_data(response)

    def _get_request_params(self, params: OptionalDict) -> dict:
        """Return dictionary with any additional authentication query parameters."""
        if params is None:
            params = {}
        params.update(self.get_client().get_default_query_params())
        return params

    def _get_request_headers(self, headers: OptionalDict) -> dict:
        """Return dictionary with any additinoal authentication headers."""
        if headers is None:
            headers = {}
        headers.update(self.get_client().get_default_headers())
        return headers

    def _get_username_password_authentication(self):
        return self.get_client().get_default_username_password_authentication()

    def _get_formatted_data(self, data: OptionalDict):
        return self.get_client().get_request_formatter().format(data)

    def _get_request_timeout(self) -> float:
        """Return the number of seconds before the request times out."""
        return self.get_client().get_request_timeout()

    def _check_response(self, response: Response):
        """Raise a custom exception if the response is not OK."""
        if response.status_code < 200 or response.status_code >= 300:
            self._handle_bad_response(response)

    def _decode_response_data(self, response: Response):
        return self.get_client().get_response_handler().get_request_data(response)

    def _handle_bad_response(self, response: Response):
        """Convert the error into an understandable client exception."""
        exception_class = self._get_exception_class(response.status_code)
        logger = self._get_logger_from_exception_type(exception_class)
        logger(
            "%s Error: %s for url: %s. data=%s",
            response.status_code,
            response.reason,
            response.url,
            response.text,
        )
        raise exception_class(
            message=f"{response.status_code} Error: {response.reason} for url: {response.url}",
            status_code=response.status_code,
        )

    @staticmethod
    def _get_exception_class(status_code: int) -> Type[exceptions.APIRequestError]:
        if 300 <= status_code < 400:
            exception_class = exceptions.RedirectionError
        elif 400 <= status_code < 500:
            exception_class = exceptions.ClientError
        elif 500 <= status_code < 600:
            exception_class = exceptions.ServerError
        else:
            exception_class = exceptions.UnexpectedError
        return exception_class

    @staticmethod
    def _get_logger_from_exception_type(exception_class) -> LOG:
        if issubclass(exception_class, exceptions.ServerError):
            return LOG.warning
        return LOG.error


class QueryParamPaginatedRequestStrategy(RequestStrategy):
    """Strategy for GET requests where pages are defined in query params."""

    def __init__(self, next_page: Callable):
        self._next_page = next_page

    def read(self, endpoint: str, params: OptionalDict = None):
        while True:

            response = super().read(endpoint, params=params)

            yield response

            next_page_params = self.get_next_page_params(response)
            if next_page_params:
                params = params if params else {}
                params.update(next_page_params)
            else:
                # No further pages found
                break

    def get_next_page_params(self, response) -> OptionalDict:
        try:
            next_page = self._next_page(response)
        except Exception:
            # Unable to get the next page from function.
            next_page = None
        return next_page


class UrlPaginatedRequestStrategy(RequestStrategy):
    """Strategy for GET requests where pages are specified by updating the endpoint."""

    def __init__(self, next_page: Callable):
        self._next_page = next_page

    def read(self, endpoint: str, params: OptionalDict = None):
        while True:
            response = super().read(endpoint, params=params)

            yield response

            next_page_url = self.get_next_page_url(response)
            if next_page_url:
                endpoint = next_page_url
            else:
                # No further pages found
                break

    def get_next_page_url(self, response) -> OptionalDict:
        try:
            next_page = self._next_page(response)
        except Exception:
            # Unable to get the next page from function.
            next_page = None
        return next_page
