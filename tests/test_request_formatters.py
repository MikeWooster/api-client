from unittest.mock import Mock

import pytest

from apiclient.request_formatters import BaseRequestFormatter, JsonRequestFormatter


class RequestFormatter(BaseRequestFormatter):
    content_type = "xml"


def test_set_client_sets_the_content_type_headers():
    client = Mock()
    client.get_default_headers.return_value = {}
    RequestFormatter.set_client(client)
    client.set_default_headers.assert_called_once_with({"Content-type": "xml"})


def test_format_method_needs_implementation():
    with pytest.raises(NotImplementedError):
        BaseRequestFormatter.format({"foo": "bar"})


def test_json_formatter_sets_json_content_type_header():
    client = Mock()
    client.get_default_headers.return_value = {}
    JsonRequestFormatter.set_client(client)
    client.set_default_headers.assert_called_once_with({"Content-type": "application/json"})


def test_json_formatter_formats_dictionary_to_json():
    data = {"foo": "bar"}
    assert JsonRequestFormatter.format(data) == '{"foo": "bar"}'


def test_json_formatter_takes_no_action_when_passed_none_type():
    data = None
    assert JsonRequestFormatter.format(data) is None
