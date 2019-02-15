import logging
from typing import Callable, Optional, Type

import requests
from requests import Response

from apiclient.authentication_methods import BaseAuthenticationMethod
from apiclient.exceptions import (
    ClientBadRequestError,
    ClientRedirectionError,
    ClientServerError,
    ClientUnexpectedError,
)
from apiclient.request_formatters import BaseRequestFormatter
from apiclient.response_handlers import BaseResponseHandler
from apiclient.utils.typing import OptionalDict

LOG = logging.getLogger(__name__)


class BaseClient:
    def __init__(
        self,
        authentication_method: BaseAuthenticationMethod,
        response_handler: Type[BaseResponseHandler],
        request_formatter: Type[BaseRequestFormatter],
    ):
        self._authentication_method = authentication_method
        self._response_handler = response_handler
        self._request_formatter = request_formatter
        self._run_initialization_checks()

        # Set default values
        self._default_headers = {}
        self._default_query_params = {}
        self._default_username_password_authentication = None

        # Allow injected dependencies to alter client.
        self._authentication_method.set_client(self)
        self._request_formatter.set_client(self)

    def _run_initialization_checks(self):
        if not isinstance(self._authentication_method, BaseAuthenticationMethod):
            raise RuntimeError(
                "provided authentication_method must be an instance of BaseAuthenticationMethod."
            )
        if not (self._response_handler and issubclass(self._response_handler, BaseResponseHandler)):
            raise RuntimeError("provided response_handler must be a subclass of BaseResponseHandler.")
        if not (self._request_formatter and issubclass(self._request_formatter, BaseRequestFormatter)):
            raise RuntimeError("provided request_formatter must be a subclass of BaseRequestFormatter.")

    def set_default_headers(self, headers: dict):
        self._default_headers = headers

    def get_default_headers(self) -> dict:
        return self._default_headers

    def set_default_query_params(self, params: dict):
        self._default_query_params = params

    def get_default_query_params(self) -> dict:
        return self._default_query_params

    def set_default_username_password_authentication(self, auth: tuple):
        self._default_username_password_authentication = auth

    def get_default_username_password_authentication(self) -> Optional[tuple]:
        return self._default_username_password_authentication

    def create(self, endpoint: str, data: dict):
        """Send data and return response data from POST endpoint."""
        LOG.info("POST %s with %s", endpoint, data)
        return self._make_request(requests.post, endpoint, data=data)

    def read(self, endpoint: str, params: OptionalDict = None):
        """Return response data from GET endpoint."""
        LOG.info("GET %s", endpoint)
        return self._make_request(requests.get, endpoint, params=params)

    def replace(self, endpoint: str, data: dict, params: OptionalDict = None):
        """Send data to overwrite resource and return response data from PUT endpoint."""
        LOG.info("PUT %s with %s", endpoint, data)
        return self._make_request(requests.put, endpoint, data=data, params=params)

    def update(self, endpoint: str, data: dict, params: OptionalDict = None):
        """Send data to update resource and return response data from PATCH endpoint."""
        LOG.info("PATCH %s with %s", endpoint, data)
        return self._make_request(requests.patch, endpoint, data=data, params=params)

    def delete(self, endpoint: str, params: OptionalDict = None):
        """Remove resource with DELETE endpoint."""
        LOG.info("DELETE %s", endpoint)
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
                auth=self.get_default_username_password_authentication(),
                data=self._request_formatter.format(data),
                **kwargs,
            )
        except Exception as error:
            LOG.error(f"An error occurred when contacting %s", endpoint, exc_info=error)
            raise ClientUnexpectedError(f"Error when contacting '{endpoint}'") from error
        else:
            self._check_response(response)
        return self._response_handler.get_request_data(response)

    def _get_request_params(self, params: OptionalDict) -> dict:
        """Return dictionary with any additional authentication query parameters."""
        if params is None:
            params = {}
        params.update(self.get_default_query_params())
        return params

    def _get_request_headers(self, headers: OptionalDict) -> dict:
        """Return dictionary with any additinoal authentication headers."""
        if headers is None:
            headers = {}
        headers.update(self.get_default_headers())
        return headers

    def _check_response(self, response: Response):
        """Raise a custom exception if the response is not OK."""
        if response.status_code < 200 or response.status_code >= 300:
            self._handle_bad_response(response)

    def _handle_bad_response(self, response: Response):
        """Convert the error into an understandable client exception."""
        logger = LOG.error
        if 300 <= response.status_code < 400:
            exception_class = ClientRedirectionError
        elif 400 <= response.status_code < 500:
            exception_class = ClientBadRequestError
        elif 500 <= response.status_code < 600:
            # Here a warning is logged instead of an error as server errors
            # are common, and can typically be retried.
            logger = LOG.warning
            exception_class = ClientServerError
        else:
            exception_class = ClientUnexpectedError
        logger(
            "%s Error: %s for url: %s. data=%s",
            response.status_code,
            response.reason,
            response.url,
            response.text,
        )
        raise exception_class(f"{response.status_code} Error: {response.reason} for url: {response.url}")
