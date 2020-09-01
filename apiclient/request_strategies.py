import logging
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Callable, Type

import aiohttp
import requests
from requests import Response

from apiclient import exceptions
from apiclient.utils.typing import OptionalDict

LOG = logging.getLogger(__name__)


if TYPE_CHECKING:  # pragma: no cover
    # Stupid way of getting around cyclic imports when
    # using typehinting.
    from apiclient import APIClient


def get_exception_class_for_status_code(status_code: int) -> Type[exceptions.APIRequestError]:
    """Translates a status code into an APIClient exception."""
    if 300 <= status_code < 400:
        exception_class = exceptions.RedirectionError
    elif 400 <= status_code < 500:
        exception_class = exceptions.ClientError
    elif 500 <= status_code < 600:
        exception_class = exceptions.ServerError
    else:
        exception_class = exceptions.UnexpectedError
    return exception_class


def get_logger_from_exception_type(exception_class) -> LOG:
    """Determines whether to log an error or warning.

    TODO: deprecate this - libraries should not log above info level.
    """
    if issubclass(exception_class, exceptions.ServerError):
        return LOG.warning
    return LOG.error


class BaseRequestStrategy:
    def __init__(self):
        self._client = None

    def set_client(self, client: "APIClient"):
        self._client = client
        # Set a global `requests.session` on the parent client instance.
        if self.get_session() is None:
            self.set_session(self.create_session())

    def create_session(self):
        """Abstract method that will create a session object."""
        raise NotImplementedError

    def get_client(self) -> "APIClient":
        return self._client

    def get_session(self):
        return self.get_client().get_session()

    def set_session(self, session: Any):
        self.get_client().set_session(session)

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

    def _check_response(self, status_code: int, reason: str, url: str, text: str) -> None:
        """Raise a custom exception if the response is not OK."""
        if status_code < 200 or status_code >= 300:
            self._handle_bad_response(status_code, reason, url, text)

    def _decode_response_data(self, content: str):
        return self.get_client().get_response_handler().get_request_data(content)

    @staticmethod
    def _handle_bad_response(status_code: int, reason: str, url: str, text: str) -> None:
        """Convert the error into an understandable client exception."""
        exception_class = get_exception_class_for_status_code(status_code)
        logger = get_logger_from_exception_type(exception_class)
        logger(
            "%s Error: %s for url: %s. data=%s", status_code, reason, url, text,
        )
        raise exception_class(
            message=f"{status_code} Error: {reason} for url: {url}", status_code=status_code,
        )

    def post(self, endpoint: str, data: dict, params: OptionalDict = None, **kwargs):
        raise NotImplementedError

    def get(self, endpoint: str, params: OptionalDict = None, **kwargs):
        raise NotImplementedError

    def put(self, endpoint: str, data: dict, params: OptionalDict = None, **kwargs):
        raise NotImplementedError

    def patch(self, endpoint: str, data: dict, params: OptionalDict = None, **kwargs):
        raise NotImplementedError

    def delete(self, endpoint: str, params: OptionalDict = None, **kwargs):
        raise NotImplementedError


class RequestStrategy(BaseRequestStrategy):
    """Requests strategy that uses the `requests` lib with a `requests.session`."""

    def create_session(self) -> requests.Session:
        return requests.session()

    def post(self, endpoint: str, data: dict, params: OptionalDict = None, **kwargs):
        """Send data and return response data from POST endpoint."""
        return self._make_request(self.get_session().post, endpoint, data=data, params=params, **kwargs)

    def get(self, endpoint: str, params: OptionalDict = None, **kwargs):
        """Return response data from GET endpoint."""
        return self._make_request(self.get_session().get, endpoint, params=params, **kwargs)

    def put(self, endpoint: str, data: dict, params: OptionalDict = None, **kwargs):
        """Send data to overwrite resource and return response data from PUT endpoint."""
        return self._make_request(self.get_session().put, endpoint, data=data, params=params, **kwargs)

    def patch(self, endpoint: str, data: dict, params: OptionalDict = None, **kwargs):
        """Send data to update resource and return response data from PATCH endpoint."""
        return self._make_request(self.get_session().patch, endpoint, data=data, params=params, **kwargs)

    def delete(self, endpoint: str, params: OptionalDict = None, **kwargs):
        """Remove resource with DELETE endpoint."""
        return self._make_request(self.get_session().delete, endpoint, params=params, **kwargs)

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
            response: Response = request_method(
                endpoint,
                params=self._get_request_params(params),
                headers=self._get_request_headers(headers),
                auth=self._get_username_password_authentication(),
                data=self._get_formatted_data(data),
                timeout=self._get_request_timeout(),
                **kwargs,
            )
        except Exception as error:
            LOG.error("An error occurred when contacting %s", endpoint, exc_info=error)
            raise exceptions.UnexpectedError(f"Error when contacting '{endpoint}'") from error
        else:
            self._check_response(response.status_code, response.reason, response.url, response.text)
        return self._decode_response_data(response.text)


class AsyncRequestStrategy(BaseRequestStrategy):
    # TODO: Figure out how to use session as context manager.?

    def create_session(self) -> aiohttp.ClientSession:
        return aiohttp.ClientSession()

    async def post(self, endpoint: str, data: dict, params: OptionalDict = None, **kwargs):
        return

    async def get(self, endpoint: str, params: OptionalDict = None, **kwargs):
        return await self._make_request(self.get_session().get, endpoint, params=params, **kwargs)

    async def put(self, endpoint: str, data: dict, params: OptionalDict = None, **kwargs):
        return

    async def patch(self, endpoint: str, data: dict, params: OptionalDict = None, **kwargs):
        return

    async def delete(self, endpoint: str, params: OptionalDict = None, **kwargs):
        return

    async def _make_request(
        self,
        request_method: Callable,
        endpoint: str,
        params: OptionalDict = None,
        headers: OptionalDict = None,
        data: OptionalDict = None,
        **kwargs,
    ) -> Response:
        try:
            async with request_method(
                endpoint,
                params=self._get_request_params(params),
                headers=self._get_request_headers(headers),
                auth=self._get_username_password_authentication(),
                data=self._get_formatted_data(data),
                timeout=self._get_request_timeout(),
                **kwargs,
            ) as response:
                self._check_response(
                    response.status, response.reason, response.url.path, await response.text()
                )
                return self._decode_response_data(await response.text())
        except Exception as error:
            LOG.error("An error occurred when contacting %s", endpoint, exc_info=error)
            raise exceptions.UnexpectedError(f"Error when contacting '{endpoint}'") from error


class QueryParamPaginatedRequestStrategy(RequestStrategy):
    """Strategy for GET requests where pages are defined in query params."""

    def __init__(self, next_page: Callable):
        self._next_page = next_page

    def get(self, endpoint: str, params: OptionalDict = None, **kwargs):
        if params is None:
            params = {}

        pages = []
        run = True
        while run:
            this_page_params = deepcopy(params)

            response = super().get(endpoint, params=this_page_params, **kwargs)

            pages.append(response)
            next_page_params = self.get_next_page_params(response, previous_page_params=this_page_params)

            if next_page_params:
                params.update(next_page_params)
            else:
                # No further pages found
                run = False

        return pages

    def get_next_page_params(self, response, previous_page_params: dict) -> OptionalDict:
        return self._next_page(response, previous_page_params)


class UrlPaginatedRequestStrategy(RequestStrategy):
    """Strategy for GET requests where pages are specified by updating the endpoint."""

    def __init__(self, next_page: Callable):
        self._next_page = next_page

    def get(self, endpoint: str, params: OptionalDict = None, **kwargs):
        pages = []
        while endpoint:
            response = super().get(endpoint, params=params, **kwargs)

            pages.append(response)

            next_page_url = self.get_next_page_url(response, previous_page_url=endpoint)
            endpoint = next_page_url

        return pages

    def get_next_page_url(self, response, previous_page_url: str) -> OptionalDict:
        return self._next_page(response, previous_page_url)
