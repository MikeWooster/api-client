import pytest
import requests

from apiclient.authentication_methods import OAuthAuthentication

TOKEN_URL = "mock://auth.testserver.com/token"


def test_fetches_and_sends_bearer_token(mock_requests):
    mock_requests.post(TOKEN_URL, json={"access_token": "abc123", "expires_in": 3600}, status_code=200)

    auth = OAuthAuthentication(token_url=TOKEN_URL, client_id="id", client_secret="secret")

    assert auth.get_headers() == {"Authorization": "Bearer abc123"}
    assert mock_requests.call_count == 1
    # The client credentials are posted to the token endpoint.
    body = mock_requests.request_history[0].text
    assert "grant_type=client_credentials" in body
    assert "client_id=id" in body
    assert "client_secret=secret" in body


def test_includes_scope_when_provided(mock_requests):
    mock_requests.post(TOKEN_URL, json={"access_token": "abc123", "expires_in": 3600}, status_code=200)

    auth = OAuthAuthentication(
        token_url=TOKEN_URL, client_id="id", client_secret="secret", scope="read write"
    )
    auth.get_headers()

    assert "scope=read+write" in mock_requests.request_history[0].text


def test_reuses_token_until_close_to_expiry(mock_requests, monkeypatch):
    mock_requests.post(TOKEN_URL, json={"access_token": "abc123", "expires_in": 3600}, status_code=200)
    clock = iter([0.0, 100.0, 200.0])
    monkeypatch.setattr("apiclient.authentication_methods.time.monotonic", lambda: next(clock))

    auth = OAuthAuthentication(token_url=TOKEN_URL, client_id="id", client_secret="secret")

    auth.get_headers()
    auth.get_headers()

    # Token is still valid, so only the initial fetch hits the token endpoint.
    assert mock_requests.call_count == 1


def test_refreshes_token_after_expiry(mock_requests, monkeypatch):
    mock_requests.post(
        TOKEN_URL,
        [
            {"json": {"access_token": "first", "expires_in": 100}, "status_code": 200},
            {"json": {"access_token": "second", "expires_in": 100}, "status_code": 200},
        ],
    )
    clock = iter([0.0, 100.0, 100.0])
    monkeypatch.setattr("apiclient.authentication_methods.time.monotonic", lambda: next(clock))

    auth = OAuthAuthentication(token_url=TOKEN_URL, client_id="id", client_secret="secret", expiry_margin=10)

    assert auth.get_headers() == {"Authorization": "Bearer first"}
    # Now past expiry (100 >= 100 - 10), so a fresh token is fetched.
    assert auth.get_headers() == {"Authorization": "Bearer second"}
    assert mock_requests.call_count == 2


def test_token_sent_without_scheme(mock_requests):
    mock_requests.post(TOKEN_URL, json={"access_token": "abc123", "expires_in": 3600}, status_code=200)

    auth = OAuthAuthentication(
        token_url=TOKEN_URL, client_id="id", client_secret="secret", parameter="X-Token", scheme=None
    )

    assert auth.get_headers() == {"X-Token": "abc123"}


def test_raises_on_token_endpoint_error(mock_requests):
    mock_requests.post(TOKEN_URL, status_code=401)

    auth = OAuthAuthentication(token_url=TOKEN_URL, client_id="id", client_secret="secret")

    with pytest.raises(requests.HTTPError):
        auth.get_headers()
