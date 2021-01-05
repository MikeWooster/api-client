from contextlib import suppress
from functools import wraps
from typing import Any, Callable, Optional, Type, TypeVar, get_type_hints

T = TypeVar("T")
with suppress(ImportError):
    from jsonmarshal import marshal, unmarshal

    def unmarshal_response(schema: T, date_fmt: Optional[str] = None, datetime_fmt: Optional[str] = None):
        """Decorator to unmarshal the response json into the provided dataclass."""

        def decorator(func) -> Callable[..., T]:
            @wraps(func)
            def wrap(*args, **kwargs) -> T:
                response = func(*args, **kwargs)
                return unmarshal(response, schema, date_fmt=date_fmt, datetime_fmt=datetime_fmt)

            return wrap

        return decorator

    def marshal_request(date_fmt: Optional[str] = None, datetime_fmt: Optional[str] = None):
        """Decorator to marshal the request from a dataclass into valid json."""

        def decorator(func) -> Callable[..., Any]:
            @wraps(func)
            def wrap(endpoint: str, data: T, *args, **kwargs):
                marshalled = marshal(data, date_fmt=date_fmt, datetime_fmt=datetime_fmt)
                return func(endpoint, marshalled, *args, **kwargs)

            return wrap

        return decorator


with suppress(ImportError):
    from pydantic import BaseModel, parse_obj_as

    def serialize_request(schema: Optional[Type[BaseModel]] = None, extra_kwargs: dict = None):
        extra_kw = extra_kwargs or {"by_alias": True, "exclude_none": True}

        def decorator(func: Callable) -> Callable:
            nonlocal schema
            map_schemas = None
            if not schema:
                map_schemas = {
                    arg_name: arg_type
                    for arg_name, arg_type in get_type_hints(func).items()
                    if arg_name not in ("return", "endpoint")
                }

            @wraps(func)
            def wrap(endpoint: str, *args, **kwargs):
                if schema:
                    instance = data = parse_obj_as(schema, kwargs)
                    if isinstance(instance, BaseModel):
                        data = instance.dict(**extra_kw)
                    return func(endpoint, data, *args)
                elif map_schemas:
                    data, origin_kwargs = {}, {}
                    for arg_name, arg_type in map_schemas.items():
                        if issubclass(arg_type, BaseModel):
                            data[arg_name] = parse_obj_as(arg_type, kwargs).dict(**extra_kw)
                        else:
                            if (val := kwargs.get(arg_name)) is not None:
                                origin_kwargs[arg_name] = val
                    return func(endpoint, **{**origin_kwargs, **data})
                return func(endpoint, *args, **kwargs)

            return wrap

        return decorator

    def serialize_response(schema: Optional[Type[BaseModel]] = None):
        def decorator(func: Callable) -> Callable:
            nonlocal schema
            if not schema:
                schema = get_type_hints(func).get("return")

            @wraps(func)
            def wrap(*args, **kwargs) -> BaseModel:
                response = func(*args, **kwargs)
                if isinstance(response, (list, dict, tuple, set)) and schema:
                    return parse_obj_as(schema, response)
                return response

            return wrap

        return decorator

    def serialize(
        schema_request: Optional[Type[BaseModel]] = None,
        schema_response: Optional[Type[BaseModel]] = None,
        **base_kwargs,
    ):
        def decorator(func: Callable) -> Callable:
            response = func
            response = serialize_request(schema_request, extra_kwargs=base_kwargs)(func)
            response = serialize_response(schema_response)(response)

            return response

        return decorator

    def serialize_all_methods(decorator=serialize):
        def decorate(cls):
            for attr, value in cls.__dict__.items():
                if callable(value) and not attr.startswith("_"):
                    setattr(cls, attr, decorator()(value))
            return cls

        return decorate
