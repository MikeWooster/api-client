import json

from apiclient.utils.typing import OptionalDict, OptionalStr


class BaseRequestFormatter:
    """Format the outgoing data accordingly and set the content-type headers."""

    content_type = None

    @classmethod
    def set_client(cls, client):
        cls._set_content_type_header(client)

    @classmethod
    def _set_content_type_header(cls, client):
        headers = client.get_default_headers()
        headers.update(cls._get_content_type_header())
        client.set_default_headers(headers)

    @classmethod
    def _get_content_type_header(cls) -> dict:
        if cls.content_type:
            return {"Content-type": cls.content_type}
        else:
            return {}

    @classmethod
    def format(cls, data: dict):
        raise NotImplementedError


class JsonRequestFormatter(BaseRequestFormatter):
    """Format the outgoing data as json."""

    content_type = "application/json"

    @classmethod
    def format(cls, data: OptionalDict) -> OptionalStr:
        if data:
            return json.dumps(data)
