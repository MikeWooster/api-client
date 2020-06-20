from typing import Dict, List, Optional, Tuple, Union
from xml.etree import ElementTree

from requests import Response

OptionalDict = Optional[dict]
OptionalStr = Optional[str]
OptionalInt = Optional[int]
BasicAuthType = Tuple[str, str]
JsonType = Union[str, int, float, dict, list]
OptionalJsonType = Optional[JsonType]
XmlType = ElementTree.Element
ResponseType = Union[JsonType, XmlType, Response]
