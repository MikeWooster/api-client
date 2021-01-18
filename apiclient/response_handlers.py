from json import JSONDecodeError
from typing import Optional
from xml.etree import ElementTree

from requests import Response

from apiclient.exceptions import ResponseParseError
from apiclient.utils.typing import JsonType, XmlType


class BaseResponseHandler:
    """Parses the response according to the strategy set."""

    @staticmethod
    def get_request_data(response: Response):
        raise NotImplementedError


class RequestsResponseHandler(BaseResponseHandler):
    """Return the original requests response."""

    @staticmethod
    def get_request_data(response: Response) -> Response:
        return response


class JsonResponseHandler(BaseResponseHandler):
    """Attempt to return the decoded response data as json."""

    @staticmethod
    def get_request_data(response: Response) -> Optional[JsonType]:
        if response.text == "":
            return None

        try:
            response_json = response.json()
        except JSONDecodeError as error:
            raise ResponseParseError(
                f"Unable to decode response data to json. data='{response.text}'"
            ) from error
        return response_json


class XmlResponseHandler(BaseResponseHandler):
    """Attempt to return the decoded response to an xml Element."""

    @staticmethod
    def get_request_data(response: Response) -> Optional[XmlType]:
        if response.text == "":
            return None

        try:
            xml_element = ElementTree.fromstring(response.text)
        except ElementTree.ParseError as error:
            raise ResponseParseError(
                f"Unable to parse response data to xml. data='{response.text}'"
            ) from error
        return xml_element
