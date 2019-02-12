

class ClientError(Exception):
    """General exception to denote that something wend wrong when using the client."""
    pass


class ClientBadRequestError(ClientError):
    """The client was used incorrectly for contacting the API.

    This is due primarily to user input by passing invalid data to the API.
    """
    pass


class ClientRedirectionError(ClientBadRequestError):
    """A redirection status code was returned as a final code when making the request.

    This means that no data can be returned to the client as we could not find the
    requested resource as it had moved.
    """
    pass


class ClientServerError(ClientError):
    """The API was unreachable when making the request."""
    pass


class ClientUnexpectedError(ClientError):
    """An unexpected error occurred when using the client."""
    pass
