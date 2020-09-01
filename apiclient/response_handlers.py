import json
import logging
from json import JSONDecodeError
from typing import TypeVar
from xml.etree import ElementTree

import yaml
from requests import Response

from apiclient.exceptions import ResponseParseError
from apiclient.utils.typing import JsonType, XmlType

LOG = logging.getLogger(__name__)

T = TypeVar("T")


class BaseResponseHandler:
    """Parses the response according to the strategy set."""

    @staticmethod
    def get_request_data(response: str):
        raise NotImplementedError


class RequestsResponseHandler(BaseResponseHandler):
    """Return the original response object."""

    @staticmethod
    def get_request_data(response: T) -> T:
        return response


class JsonResponseHandler(BaseResponseHandler):
    """Attempt to return the decoded response data as json."""

    @staticmethod
    def get_request_data(content: str) -> JsonType:
        try:
            response_json = json.loads(content)
        except JSONDecodeError as error:
            LOG.error("Unable to decode response data to json. data=%s", content)
            raise ResponseParseError(f"Unable to decode response data to json. data='{content}'") from error
        return response_json


class XmlResponseHandler(BaseResponseHandler):
    """Attempt to return the decoded response to an xml Element."""

    @staticmethod
    def get_request_data(content: str) -> XmlType:
        try:
            xml_element = ElementTree.fromstring(content)
        except ElementTree.ParseError as error:
            LOG.error("Unable to parse response data to xml. data=%s", content)
            raise ResponseParseError(f"Unable to parse response data to xml. data='{content}'") from error
        return xml_element


class YamlResponseHandler(BaseResponseHandler):
    """Attempt to return the decoded response as yaml."""

    @staticmethod
    def get_request_data(content: str) -> JsonType:
        try:
            response_yaml = yaml.load(content)
        except yaml.YAMLError as error:
            LOG.error("Unable to parse response data to yaml. data=%s", content)
            raise ResponseParseError(f"Unable to parse response data to yaml. data='{content}'") from error
        return response_yaml
