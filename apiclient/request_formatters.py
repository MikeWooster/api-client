import json

from apiclient.utils.typing import JsonType


class BaseRequestFormatter:
    """Format the outgoing data accordingly and set the content-type headers."""

    content_type = None

    @classmethod
    def get_headers(cls) -> dict:
        if cls.content_type:
            return {"Content-type": cls.content_type}
        else:
            return {}

    @classmethod
    def format(cls, data: JsonType | None):
        raise NotImplementedError


class NoOpRequestFormatter(BaseRequestFormatter):
    """No action request formatter."""

    @classmethod
    def format(cls, data: JsonType | None) -> JsonType | None:
        return data


class JsonRequestFormatter(BaseRequestFormatter):
    """Format the outgoing data as json."""

    content_type = "application/json"

    @classmethod
    def format(cls, data: JsonType | None) -> str | None:
        if data:
            return json.dumps(data)
