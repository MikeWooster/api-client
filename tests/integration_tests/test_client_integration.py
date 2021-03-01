# Integration tests using all request methods on a
# real world api client with all methods implemented

import pytest

from apiclient import JsonRequestFormatter, JsonResponseHandler, NoAuthentication
from apiclient.exceptions import ClientError, RedirectionError, ServerError, UnexpectedError
from tests.integration_tests.client import Client, ClientErrorHandler, InternalError, OtherError, Urls


def test_client_response(cassette):
    client = Client(
        authentication_method=NoAuthentication(),
        response_handler=JsonResponseHandler,
        request_formatter=JsonRequestFormatter,
    )
    users = client.list_users()
    assert len(users) == 3
    assert users == [
        {"userId": 1, "firstName": "Mike", "lastName": "Foo"},
        {"userId": 2, "firstName": "Sarah", "lastName": "Bar"},
        {"userId": 3, "firstName": "Barry", "lastName": "Baz"},
    ]
    assert cassette.play_count == 1

    # User 1 requested successfully on first attempt
    user = client.get_user(user_id=1)
    assert user == {"userId": 1, "firstName": "Mike", "lastName": "Foo"}
    assert cassette.play_count == 2

    # User 2 failed on first attempt, succeeded on second
    user = client.get_user(user_id=2)
    assert user == {"userId": 2, "firstName": "Sarah", "lastName": "Bar"}
    assert cassette.play_count == 4

    new_user = client.create_user(first_name="Lucy", last_name="Qux")
    assert new_user == {"userId": 4, "firstName": "Lucy", "lastName": "Qux"}
    assert cassette.play_count == 5

    overwritten_user = client.overwrite_user(user_id=4, first_name="Lucy", last_name="Foo")
    assert overwritten_user == {"userId": 4, "firstName": "Lucy", "lastName": "Foo"}
    assert cassette.play_count == 6

    updated_user = client.update_user(user_id=4, first_name="Lucy", last_name="Qux")
    assert updated_user == {"userId": 4, "firstName": "Lucy", "lastName": "Qux"}
    assert cassette.play_count == 7

    # DELETE cassette doesn't seem to be working correctly.
    # deleted_user = client.delete_user(user_id=4)
    # assert deleted_user is None
    # assert cassette.play_count == 8

    pages = list(client.list_user_accounts_paginated(user_id=1))
    assert len(pages) == 3
    assert pages == [
        {
            "results": [
                {"accountName": "business", "number": "1234"},
                {"accountName": "expense", "number": "2345"},
            ],
            "page": 1,
            "nextPage": 2,
        },
        {
            "results": [
                {"accountName": "fun", "number": "6544"},
                {"accountName": "holiday", "number": "9283"},
            ],
            "page": 2,
            "nextPage": 3,
        },
        {
            "results": [
                {"accountName": "gifts", "number": "7827"},
                {"accountName": "home", "number": "1259"},
            ],
            "page": 3,
            "nextPage": None,
        },
    ]

    # Fails to connect when connecting to non-existent url.
    with pytest.raises(UnexpectedError) as exc_info:
        client.get("mock://testserver")
    assert str(exc_info.value) == "Error when contacting 'mock://testserver'"

    # User 10 failed on first attempt 500 with 20001 code
    client.set_error_handler(ClientErrorHandler)
    with pytest.raises(InternalError) as exc_info:
        client.list_user_accounts_paginated(user_id=10)
    assert str(exc_info.value) == "Internal error."
    # failed on second 400 with 20002 code
    with pytest.raises(OtherError) as exc_info:
        client.list_user_accounts_paginated(user_id=10)
    assert str(exc_info.value) == "Other error."
    # failed on third 500 with no_code
    with pytest.raises(ServerError) as exc_info:
        client.list_user_accounts_paginated(user_id=10)
    assert str(exc_info.value) == "500 Error: SERVER ERROR for url: http://testserver/accounts?userId=10"
    # and 504 with html body
    with pytest.raises(ServerError) as exc_info:
        client.list_user_accounts_paginated(user_id=10)
    assert str(exc_info.value) == "504 Error: SERVER ERROR for url: http://testserver/accounts?userId=10"
    # and 500 with empty body
    with pytest.raises(ServerError) as exc_info:
        client.list_user_accounts_paginated(user_id=10)
    assert str(exc_info.value) == "500 Error: SERVER ERROR for url: http://testserver/accounts?userId=10"


@pytest.mark.parametrize(
    "user_id,expected_error,expected_message",
    [
        (1, RedirectionError, "300 Error: REDIRECT for url: http://testserver/users/1"),
        (2, RedirectionError, "399 Error: REDIRECT for url: http://testserver/users/2"),
        (3, ClientError, "400 Error: CLIENT ERROR for url: http://testserver/users/3"),
        (4, ClientError, "499 Error: CLIENT ERROR for url: http://testserver/users/4"),
        (5, ServerError, "500 Error: SERVER ERROR for url: http://testserver/users/5"),
        (6, ServerError, "599 Error: SERVER ERROR for url: http://testserver/users/6"),
        (7, UnexpectedError, "600 Error: UNEXPECTED for url: http://testserver/users/7"),
        (8, UnexpectedError, "999 Error: UNEXPECTED for url: http://testserver/users/8"),
    ],
)
def test_bad_response_error_codes(user_id, expected_error, expected_message, error_cassette):
    # Error cassette has been configured so that different users respond with different error codes

    client = Client(
        authentication_method=NoAuthentication(),
        response_handler=JsonResponseHandler,
        request_formatter=JsonRequestFormatter,
    )

    url = Urls.user.format(id=user_id)

    # Test GET request
    with pytest.raises(expected_error) as exc_info:
        client.get(url)
    assert str(exc_info.value) == expected_message

    error_cassette.rewind()

    # Test POST request
    with pytest.raises(expected_error) as exc_info:
        client.post(url, data={"clientId": "1234"})
    assert str(exc_info.value) == expected_message

    error_cassette.rewind()

    # Test PUT request
    with pytest.raises(expected_error) as exc_info:
        client.put(url, data={"clientId": "1234"})
    assert str(exc_info.value) == expected_message

    error_cassette.rewind()

    # Test PATCH request
    with pytest.raises(expected_error) as exc_info:
        client.patch(url, data={"clientId": "1234"})
    assert str(exc_info.value) == expected_message

    error_cassette.rewind()

    # Test DELETE request
    with pytest.raises(expected_error) as exc_info:
        client.delete(url)
    assert str(exc_info.value) == expected_message
