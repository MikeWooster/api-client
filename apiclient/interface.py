"""Defines the public interface to the client."""


class IClient:  # pragma: no cover
    def set_authentication_method(self, *args, **kwargs):
        raise NotImplementedError

    def get_response_handler(self):
        raise NotImplementedError

    def set_response_handler(self, *args, **kwargs):
        raise NotImplementedError

    def get_request_formatter(self):
        raise NotImplementedError

    def set_request_formatter(self, *args, **kwargs):
        raise NotImplementedError

    def get_request_strategy(self):
        raise NotImplementedError

    def set_request_strategy(self, *args, **kwargs):
        raise NotImplementedError

    def get_default_headers(self):
        raise NotImplementedError

    def get_default_query_params(self):
        raise NotImplementedError

    def get_default_username_password_authentication(self):
        raise NotImplementedError

    def get_request_timeout(self):
        raise NotImplementedError

    def clone(self):
        raise NotImplementedError

    def create(self, *args, **kwargs):
        raise NotImplementedError

    def read(self, *args, **kwargs):
        raise NotImplementedError

    def replace(self, *args, **kwargs):
        raise NotImplementedError

    def update(self, *args, **kwargs):
        raise NotImplementedError

    def delete(self, *args, **kwargs):
        raise NotImplementedError
