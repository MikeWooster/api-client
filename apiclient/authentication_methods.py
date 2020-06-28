import http.cookiejar
from typing import TYPE_CHECKING, Dict, Optional, Union

from apiclient.utils.typing import BasicAuthType, OptionalStr

if TYPE_CHECKING:  # pragma: no cover
    # Stupid way of getting around cyclic imports when
    # using typehinting.
    from apiclient import APIClient


class BaseAuthenticationMethod:
    def get_headers(self) -> dict:
        return {}

    def get_query_params(self) -> dict:
        return {}

    def get_username_password_authentication(self) -> Optional[BasicAuthType]:
        return None

    def perform_initial_auth(self, client: "APIClient"):
        pass


class NoAuthentication(BaseAuthenticationMethod):
    """No authentication methods needed for API."""

    pass


class QueryParameterAuthentication(BaseAuthenticationMethod):
    """Authentication provided as part of the query parameter."""

    def __init__(self, parameter: str, token: str):
        self._parameter = parameter
        self._token = token

    def get_query_params(self):
        return {self._parameter: self._token}


class HeaderAuthentication(BaseAuthenticationMethod):
    """Authentication provided within the header.

    Normally associated with Oauth authoriazation, in the format:
    "Authorization: Bearer <token>"
    """

    def __init__(
        self,
        token: str,
        parameter: str = "Authorization",
        scheme: OptionalStr = "Bearer",
        extra: Optional[Dict[str, str]] = None,
    ):
        self._token = token
        self._parameter = parameter
        self._scheme = scheme
        self._extra = extra

    def get_headers(self) -> Dict[str, str]:
        if self._scheme:
            headers = {self._parameter: f"{self._scheme} {self._token}"}
        else:
            headers = {self._parameter: self._token}
        if self._extra:
            headers.update(self._extra)
        return headers


class BasicAuthentication(BaseAuthenticationMethod):
    """Authentication provided in the form of a username/password."""

    def __init__(self, username: str, password: str):
        self._username = username
        self._password = password

    def get_username_password_authentication(self) -> BasicAuthType:
        return (self._username, self._password)


class CookieAuthentication(BaseAuthenticationMethod):
    """Authentication stored as Cookie after accessing URL using GET."""

    def __init__(
        self,
        auth_url: str,
        authentication: Union[HeaderAuthentication, QueryParameterAuthentication, BasicAuthentication],
    ):
        self._auth_url = auth_url
        self._authentication = authentication

    def perform_initial_auth(self, client: "APIClient"):
        client.get(
            self._auth_url,
            headers=self._authentication.get_headers(),
            params=self._authentication.get_query_params(),
            cookies=http.cookiejar.CookieJar(),
        )
