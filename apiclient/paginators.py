from contextlib import contextmanager
from functools import wraps
from typing import Callable

from apiclient import APIClient
from apiclient.request_strategies import (
    BaseRequestStrategy,
    QueryParamPaginatedRequestStrategy,
    UrlPaginatedRequestStrategy,
)


@contextmanager
def set_strategy(client: APIClient, strategy: BaseRequestStrategy):
    """Set a strategy on the client and then set it back after running."""
    temporary_client = client.clone()
    temporary_client.set_request_strategy(strategy)
    try:
        yield temporary_client
    finally:
        del temporary_client


def paginated(by_query_params: Callable = None, by_url: Callable = None):
    """Decorator to signal that the page is paginated."""
    if by_query_params:
        strategy = QueryParamPaginatedRequestStrategy(by_query_params)
    else:
        strategy = UrlPaginatedRequestStrategy(by_url)

    def decorator(func):
        @wraps(func)
        def wrap(client: APIClient, *args, **kwargs):
            with set_strategy(client, strategy) as temporary_client:
                return func(temporary_client, *args, **kwargs)

        return wrap

    return decorator
