
# This defines the base url in the endpoint and must be present.
BASE_URL_RESERVED_NAME = "base_url"


def endpoint(cls=None):
    """Decorator for automatically constructing urls from a base_url and defined resources."""
    def wrap(cls):
        return _process_class(cls)
    if cls is None:
        # Decorator is called as @endpoint with parens.
        return wrap
    # Decorator is called as @endpoint without parens.
    return wrap(cls)


def _process_class(cls):
    if BASE_URL_RESERVED_NAME not in cls.__dict__:
        raise RuntimeError("An Endpoint must define a `base_url`.")

    base_url = str(cls.__dict__[BASE_URL_RESERVED_NAME]).rstrip("/")

    for name, value in cls.__dict__.items():
        if name.startswith("_") or name == BASE_URL_RESERVED_NAME:
            # Ignore any private or class attributes.
            continue
        new_value = str(value).lstrip("/")
        resource = f"{base_url}/{new_value}"
        setattr(cls, name, resource)
    return cls
