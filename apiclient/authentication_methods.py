from typing import Optional

from apiclient.utils.typing import BasicAuthType


class BaseAuthenticationMethod:

    def set_client(self, client):
        self._client = client
        self.add_authentication_headers()
        self.add_authentication_params()
        self.add_username_password_authentication()

    def get_authentication_headers(self) -> dict:
        return {}

    def add_authentication_headers(self):
        headers = self._client.get_default_headers()
        headers.update(self.get_authentication_headers())
        self._client.set_default_headers(headers)

    def get_authentication_params(self) -> dict:
        return {}

    def add_authentication_params(self):
        params = self._client.get_default_query_params()
        params.update(self.get_authentication_params())
        self._client.set_default_query_params(params)

    def get_username_password_authentication(self) -> Optional[BasicAuthType]:
        return None

    def add_username_password_authentication(self):
        auth = self.get_username_password_authentication()
        self._client.set_default_username_password_authentication(auth)


class NoAuthentication(BaseAuthenticationMethod):
    """No authentication methods needed for API."""

    pass


class QueryParameterAuthentication(BaseAuthenticationMethod):
    """Authentication provided as part of the query parameter."""

    def __init__(self, parameter: str, token: str):
        self._parameter = parameter
        self._token = token

    def get_authentication_params(self):
        return {self._parameter: self._token}


class HeaderAuthentication(BaseAuthenticationMethod):
    """Authentication provided within the header.

    Normally associated with Oauth authoriazation, in the format:
    "Authorization: Bearer <token>"
    """

    def __init__(self, token: str, parameter: str = "Authorization", realm: str = "Bearer"):
        self._token = token
        self._parameter = parameter
        self._realm = realm

    def get_authentication_headers(self):
        return {self._parameter: f"{self._realm} {self._token}"}


class BasicAuthentication(BaseAuthenticationMethod):
    """Authentication provided in the form of a username/password."""

    def __init__(self, username: str, password: str):
        self._username = username
        self._password = password

    def get_username_password_authentication(self) -> BasicAuthType:
        return (self._username, self._password)
