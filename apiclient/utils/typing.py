from xml.etree import ElementTree

from requests import Response

BasicAuthType = tuple[str, str]
JsonType = str | list | dict
XmlType = ElementTree.Element
ResponseType = JsonType | XmlType | Response
