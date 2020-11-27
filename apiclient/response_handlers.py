from json import JSONDecodeError
from typing import Optional
from xml.etree import ElementTree

import yaml
from requests import Response

from apiclient.exceptions import ResponseParseError
from apiclient.utils.typing import JsonType, XmlType
from apiclient.utils.warnings import deprecation_warning


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


class YamlResponseHandler(BaseResponseHandler):
    """Attempt to return the decoded response as yaml."""

    @staticmethod
    def get_request_data(response: Response) -> JsonType:
        deprecation_warning("YamlResponseHandler will be removed in version 1.3.0")

        try:
            response_yaml = yaml.load(response.text)
        except yaml.YAMLError as error:
            raise ResponseParseError(
                f"Unable to parse response data to yaml. data='{response.text}'"
            ) from error
        return response_yaml
