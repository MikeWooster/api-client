from typing import Optional

from apiclient.utils.typing import BasicAuthType, OptionalStr


class BaseAuthenticationMethod:
    def get_headers(self) -> dict:
        return {}

    def get_query_params(self) -> dict:
        return {}

    def get_username_password_authentication(self) -> Optional[BasicAuthType]:
        return None


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

    def __init__(self, token: str, parameter: str = "Authorization", scheme: OptionalStr = "Bearer"):
        self._token = token
        self._parameter = parameter
        self._scheme = scheme

    def get_headers(self):
        if self._scheme:
            return {self._parameter: f"{self._scheme} {self._token}"}
        else:
            return {self._parameter: self._token}


class BasicAuthentication(BaseAuthenticationMethod):
    """Authentication provided in the form of a username/password."""

    def __init__(self, username: str, password: str):
        self._username = username
        self._password = password

    def get_username_password_authentication(self) -> BasicAuthType:
        return (self._username, self._password)
