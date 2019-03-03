class APIClientError(Exception):
    """General exception to denote that something went wrong when using the client."""

    pass


class RedirectionError(APIClientError):
    """A redirection status code (3xx) was returned as a final code when making the request.

    This means that no data can be returned to the client as we could not find the
    requested resource as it had moved.
    """

    pass


class ClientError(APIClientError):
    """A client error status code (4xx) was returned as a final code when making the request.

    This is due primarily to user input by passing invalid data to the API
    """

    pass


class ServerError(APIClientError):
    """A server error status code (5xx) was returned as a final code when making the request.

    This will mainly due to the server being uncontactable when making the request.
    """

    pass


class UnexpectedError(APIClientError):
    """An unexpected error occurred when using the client."""

    pass


# ---------------------------------------------------------------------
# The following group of exceptions are all types of Redirection Error.
# ---------------------------------------------------------------------


class MultipleChoices(RedirectionError):
    """The client received a 300 status code when making the request."""

    pass


class MovedPermanently(RedirectionError):
    """The client received a 301 status code when making the request."""

    pass


class Found(RedirectionError):
    """The client received a 302 status code when making the request."""

    pass


class SeeOther(RedirectionError):
    """The client received a 303 status code when making the request."""

    pass


class NotModified(RedirectionError):
    """The client received a 304 status code when making the request."""

    pass


class UseProxy(RedirectionError):
    """The client received a 305 status code when making the request."""

    pass


class TemporaryRedirect(RedirectionError):
    """The client received a 307 status code when making the request."""

    pass


class PermanentRedirect(RedirectionError):
    """The client received a 308 status code when making the request."""

    pass


# ---------------------------------------------------------------------
# The following group of exceptions are all types of Client Error.
# ---------------------------------------------------------------------


class BadRequest(ClientError):
    """The client received a 400 status code when making the request."""

    pass


class Unauthorized(ClientError):
    """The client received a 401 status code when making the request."""

    pass


class PaymentRequired(ClientError):
    """The client received a 402 status code when making the request."""

    pass


class Forbidden(ClientError):
    """The client received a 403 status code when making the request."""

    pass


class NotFound(ClientError):
    """The client received a 404 status code when making the request."""

    pass


class MethodNotAllowed(ClientError):
    """The client received a 405 status code when making the request."""

    pass


class NotAcceptable(ClientError):
    """The client received a 406 status code when making the request."""

    pass


class ProxyAuthenticationRequired(ClientError):
    """The client received a 407 status code when making the request."""

    pass


class RequestTimeout(ClientError):
    """The client received a 408 status code when making the request."""

    pass


class Conflict(ClientError):
    """The client received a 409 status code when making the request."""

    pass


class Gone(ClientError):
    """The client received a 410 status code when making the request."""

    pass


class LengthRequired(ClientError):
    """The client received a 411 status code when making the request."""

    pass


class PreconditionFailed(ClientError):
    """The client received a 412 status code when making the request."""

    pass


class RequestEntityTooLarge(ClientError):
    """The client received a 413 status code when making the request."""

    pass


class RequestUriTooLong(ClientError):
    """The client received a 414 status code when making the request."""

    pass


class UnsupportedMediaType(ClientError):
    """The client received a 415 status code when making the request."""

    pass


class RequestedRangeNotSatisfiable(ClientError):
    """The client received a 416 status code when making the request."""

    pass


class ExpectationFailed(ClientError):
    """The client received a 417 status code when making the request."""

    pass


class UnprocessableEntity(ClientError):
    """The client received a 422 status code when making the request."""

    pass


class Locked(ClientError):
    """The client received a 423 status code when making the request."""

    pass


class FailedDependency(ClientError):
    """The client received a 424 status code when making the request."""

    pass


class UpgradeRequired(ClientError):
    """The client received a 426 status code when making the request."""

    pass


class PreconditionRequired(ClientError):
    """The client received a 428 status code when making the request."""

    pass


class TooManyRequests(ClientError):
    """The client received a 429 status code when making the request."""

    pass


class RequestHeaderFieldsTooLarge(ClientError):
    """The client received a 431 status code when making the request."""

    pass


# ---------------------------------------------------------------------
# The following group of exceptions are all types of Server Error.
# ---------------------------------------------------------------------


class InternalServerError(ServerError):
    """The client received a 500 status code when making the request."""

    pass


class NotImplemented(ServerError):
    """The client received a 501 status code when making the request."""

    pass


class BadGateway(ServerError):
    """The client received a 502 status code when making the request."""

    pass


class ServiceUnavailable(ServerError):
    """The client received a 503 status code when making the request."""

    pass


class GatewayTimeout(ServerError):
    """The client received a 504 status code when making the request."""

    pass


class HttpVersionNotSupported(ServerError):
    """The client received a 505 status code when making the request."""

    pass


class VariantAlsoNegotiates(ServerError):
    """The client received a 506 status code when making the request."""

    pass


class InsufficientStorage(ServerError):
    """The client received a 507 status code when making the request."""

    pass


class LoopDetected(ServerError):
    """The client received a 508 status code when making the request."""

    pass


class NotExtended(ServerError):
    """The client received a 510 status code when making the request."""

    pass


class NetworkAuthenticationRequired(ServerError):
    """The client received a 511 status code when making the request."""

    pass
