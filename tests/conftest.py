import os
from dataclasses import dataclass
from unittest.mock import Mock, sentinel

import pytest
import requests_mock
import vcr

from apiclient import APIClient
from apiclient.request_formatters import BaseRequestFormatter
from apiclient.response_handlers import BaseResponseHandler

BASE_DIR = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
VCR_CASSETTE_DIR = os.path.join(BASE_DIR, "vcr_cassettes")


api_client_vcr = vcr.VCR(
    serializer="yaml",
    cassette_library_dir=VCR_CASSETTE_DIR,
    record_mode="once",
    match_on=["uri", "method", "query"],
)

error_cassette_vcr = vcr.VCR(
    serializer="yaml", cassette_library_dir=VCR_CASSETTE_DIR, record_mode="once", match_on=["uri"]
)


@pytest.fixture
def cassette():
    with api_client_vcr.use_cassette("cassette.yaml") as cassette:
        yield cassette


@pytest.fixture
def error_cassette():
    with error_cassette_vcr.use_cassette("error_cassette.yaml") as cassette:
        yield cassette


@pytest.fixture
def mock_requests():
    with requests_mock.mock() as _mocker:
        yield _mocker


@dataclass
class MockClient:
    client: Mock
    request_formatter: Mock
    response_handler: Mock


@pytest.fixture
def mock_client():
    # Build our fully mocked client
    _mock_client: APIClient = Mock(spec=APIClient)
    mock_request_formatter: BaseRequestFormatter = Mock(spec=BaseRequestFormatter)
    mock_response_handler: BaseResponseHandler = Mock(spec=BaseResponseHandler)
    _mock_client.get_default_query_params.return_value = {}
    _mock_client.get_default_headers.return_value = {}
    _mock_client.get_default_username_password_authentication.return_value = None
    _mock_client.get_request_timeout.return_value = 30.0
    mock_request_formatter.format.return_value = {}
    _mock_client.get_request_formatter.return_value = mock_request_formatter
    mock_response_handler.get_request_data.return_value = sentinel.result
    _mock_client.get_response_handler.return_value = mock_response_handler

    return MockClient(
        client=_mock_client, request_formatter=mock_request_formatter, response_handler=mock_response_handler
    )
