from typing import Optional, TypeVar

from jsonmarshal import marshal, unmarshal

T = TypeVar("T")


def unmarshal_response(schema: T, date_fmt: Optional[str] = None, datetime_fmt: Optional[str] = None):
    """Decorator to unmarshal the response json into the provided dataclass."""

    def decorator(func) -> T:
        def wrap(*args, **kwargs) -> T:
            response = func(*args, **kwargs)
            return unmarshal(response, schema, date_fmt=date_fmt, datetime_fmt=datetime_fmt)

        return wrap

    return decorator


def marshal_request(date_fmt: Optional[str] = None, datetime_fmt: Optional[str] = None):
    """Decorator to marshal the request from a dataclass into valid json."""

    def decorator(func) -> T:
        def wrap(endpoint: str, data: T, *args, **kwargs):
            marshalled = marshal(data, date_fmt=date_fmt, datetime_fmt=datetime_fmt)
            return func(endpoint, marshalled, *args, **kwargs)

        return wrap

    return decorator
