from unittest.mock import sentinel

import pytest

from apiclient import JsonRequestFormatter
from apiclient.request_formatters import BaseRequestFormatter, NoOpRequestFormatter


class RequestFormatter(BaseRequestFormatter):
    content_type = "xml"


def test_format_method_needs_implementation():
    with pytest.raises(NotImplementedError):
        BaseRequestFormatter.format({"foo": "bar"})


def test_json_formatter_formats_dictionary_to_json():
    data = {"foo": "bar"}
    assert JsonRequestFormatter.format(data) == '{"foo": "bar"}'


def test_json_formatter_takes_no_action_when_passed_none_type():
    data = None
    assert JsonRequestFormatter.format(data) is None


def test_no_op_formatter_proxies_input():
    assert NoOpRequestFormatter.format(sentinel.data) == sentinel.data
