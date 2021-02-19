from json import JSONDecodeError
from typing import Optional
from xml.etree import ElementTree

import requests

from apiclient.exceptions import ResponseParseError
from apiclient.response import Response
from apiclient.utils.typing import JsonType, XmlType


class BaseResponseHandler:
    """Parses the response according to the strategy set."""

    @staticmethod
    def get_request_data(response: Response):
        raise NotImplementedError


class RequestsResponseHandler(BaseResponseHandler):
    """Return the original requests response."""

    @staticmethod
    def get_request_data(response: Response) -> requests.Response:
        return response.get_original()


class JsonResponseHandler(BaseResponseHandler):
    """Attempt to return the decoded response data as json."""

    @staticmethod
    def get_request_data(response: Response) -> Optional[JsonType]:
        if response.get_raw_data() == "":
            return None

        try:
            response_json = response.get_json()
        except JSONDecodeError as error:
            raise ResponseParseError(
                f"Unable to decode response data to json. data='{response.get_raw_data()}'"
            ) from error
        return response_json


class XmlResponseHandler(BaseResponseHandler):
    """Attempt to return the decoded response to an xml Element."""

    @staticmethod
    def get_request_data(response: Response) -> Optional[XmlType]:
        if response.get_raw_data() == "":
            return None

        try:
            xml_element = ElementTree.fromstring(response.get_raw_data())
        except ElementTree.ParseError as error:
            raise ResponseParseError(
                f"Unable to parse response data to xml. data='{response.get_raw_data()}'"
            ) from error
        return xml_element
