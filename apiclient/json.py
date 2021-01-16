from typing import Any, Callable, Optional, TypeVar

from jsonmarshal import marshal, unmarshal

from apiclient.utils.warnings import deprecation_warning

T = TypeVar("T")


def unmarshal_response(schema: T, date_fmt: Optional[str] = None, datetime_fmt: Optional[str] = None):
    """Decorator to unmarshal the response json into the provided dataclass."""
    deprecation_warning(
        "unmarshal_response will be removed in version 1.3.0. "
        "Update all imports to `from apiclient_jsonmarshal import unmarshal_response`."
    )

    def decorator(func) -> Callable[..., T]:
        def wrap(*args, **kwargs) -> T:
            response = func(*args, **kwargs)
            return unmarshal(response, schema, date_fmt=date_fmt, datetime_fmt=datetime_fmt)

        return wrap

    return decorator


def marshal_request(date_fmt: Optional[str] = None, datetime_fmt: Optional[str] = None):
    """Decorator to marshal the request from a dataclass into valid json."""
    deprecation_warning(
        "marshal_request will be removed in version 1.3.0. "
        "Update all imports to `from apiclient_jsonmarshal import marshal_request`."
    )

    def decorator(func) -> Callable[..., Any]:
        def wrap(endpoint: str, data: T, *args, **kwargs):
            marshalled = marshal(data, date_fmt=date_fmt, datetime_fmt=datetime_fmt)
            return func(endpoint, marshalled, *args, **kwargs)

        return wrap

    return decorator
