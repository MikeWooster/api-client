import json

from apiclient.utils.typing import OptionalJsonType, OptionalStr


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
    def format(cls, data: OptionalJsonType):
        raise NotImplementedError


class JsonRequestFormatter(BaseRequestFormatter):
    """Format the outgoing data as json."""

    content_type = "application/json"

    @classmethod
    def format(cls, data: OptionalJsonType) -> OptionalStr:
        if data:
            return json.dumps(data)
