import os

import pytest
import vcr


BASE_DIR = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
VCR_CASSETTE_DIR = os.path.join(BASE_DIR, "vcr_cassettes")


api_client_vcr = vcr.VCR(
    serializer="yaml", cassette_library_dir=VCR_CASSETTE_DIR, record_mode="once", match_on=["uri", "method"]
)


@pytest.fixture
def json_placeholder_cassette():
    with api_client_vcr.use_cassette("json_placeholder_cassette.yaml") as cassette:
        yield cassette
