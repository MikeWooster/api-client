# Integration tests using all request methods on a
# real world api client with all methods implemented

import pytest

from apiclient import JsonRequestFormatter, JsonResponseHandler, NoAuthentication
from apiclient.exceptions import ClientError, RedirectionError, ServerError, UnexpectedError
from tests.integration_tests.client import (
    Account,
    AccountPage,
    Client,
    ClientWithJson,
    ClientWithPydantic,
    PDAccount,
    PDAccountPage,
    PDUser,
    Urls,
    User,
)


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


def test_client_response_with_jsonmarshal(cassette):

    client = ClientWithJson(
        authentication_method=NoAuthentication(),
        response_handler=JsonResponseHandler,
        request_formatter=JsonRequestFormatter,
    )
    users = client.list_users()
    assert len(users) == 3
    assert users == [
        User(user_id=1, first_name="Mike", last_name="Foo"),
        User(user_id=2, first_name="Sarah", last_name="Bar"),
        User(user_id=3, first_name="Barry", last_name="Baz"),
    ]
    assert cassette.play_count == 1

    # User 1 requested successfully on first attempt
    user = client.get_user(user_id=1)
    assert user == User(user_id=1, first_name="Mike", last_name="Foo")
    assert cassette.play_count == 2

    # User 2 failed on first attempt, succeeded on second
    user = client.get_user(user_id=2)
    assert user == User(user_id=2, first_name="Sarah", last_name="Bar")

    assert cassette.play_count == 4

    new_user = client.create_user(first_name="Lucy", last_name="Qux")
    assert new_user == User(user_id=4, first_name="Lucy", last_name="Qux")

    assert cassette.play_count == 5

    overwritten_user = client.overwrite_user(user_id=4, first_name="Lucy", last_name="Foo")
    assert overwritten_user == User(user_id=4, first_name="Lucy", last_name="Foo")
    assert cassette.play_count == 6

    updated_user = client.update_user(user_id=4, first_name="Lucy", last_name="Qux")
    assert updated_user == User(user_id=4, first_name="Lucy", last_name="Qux")
    assert cassette.play_count == 7

    # DELETE cassette doesn't seem to be working correctly.
    # deleted_user = client.delete_user(user_id=4)
    # assert deleted_user is None
    # assert cassette.play_count == 8

    # paginated responds with a generator, so need to cast to list.
    pages = list(client.list_user_accounts_paginated(user_id=1))
    assert len(pages) == 3
    assert pages == [
        AccountPage(
            results=[
                Account(account_name="business", number="1234"),
                Account(account_name="expense", number="2345"),
            ],
            page=1,
            next_page=2,
        ),
        AccountPage(
            results=[
                Account(account_name="fun", number="6544"),
                Account(account_name="holiday", number="9283"),
            ],
            page=2,
            next_page=3,
        ),
        AccountPage(
            results=[
                Account(account_name="gifts", number="7827"),
                Account(account_name="home", number="1259"),
            ],
            page=3,
            next_page=None,
        ),
    ]

    # Fails to connect when connecting to non-existent url.
    with pytest.raises(UnexpectedError) as exc_info:
        client.get("mock://testserver")
    assert str(exc_info.value) == "Error when contacting 'mock://testserver'"


def test_client_response_with_pydantic(cassette):

    client = ClientWithPydantic(
        authentication_method=NoAuthentication(),
        response_handler=JsonResponseHandler,
        request_formatter=JsonRequestFormatter,
    )
    users = client.list_users()
    assert len(users) == 3
    assert users == [
        PDUser(user_id=1, first_name="Mike", last_name="Foo"),
        PDUser(user_id=2, first_name="Sarah", last_name="Bar"),
        PDUser(user_id=3, first_name="Barry", last_name="Baz"),
    ]
    assert cassette.play_count == 1

    # User 1 requested successfully on first attempt
    user = client.get_user(user_id=1)
    assert user == PDUser(user_id=1, first_name="Mike", last_name="Foo")
    assert cassette.play_count == 2

    # User 2 failed on first attempt, succeeded on second
    user = client.get_user(user_id=2)
    assert user == PDUser(user_id=2, first_name="Sarah", last_name="Bar")

    assert cassette.play_count == 4

    new_user = client.create_user(first_name="Lucy", last_name="Qux")
    assert new_user == PDUser(user_id=4, first_name="Lucy", last_name="Qux")

    assert cassette.play_count == 5

    overwritten_user = client.overwrite_user(user_id=4, first_name="Lucy", last_name="Foo")
    assert overwritten_user == PDUser(user_id=4, first_name="Lucy", last_name="Foo")
    assert cassette.play_count == 6

    updated_user = client.update_user(user_id=4, first_name="Lucy", last_name="Qux")
    assert updated_user == PDUser(user_id=4, first_name="Lucy", last_name="Qux")
    assert cassette.play_count == 7

    # DELETE cassette doesn't seem to be working correctly.
    # deleted_user = client.delete_user(user_id=4)
    # assert deleted_user is None
    # assert cassette.play_count == 8

    # paginated responds with a generator, so need to cast to list.
    pages = list(client.list_user_accounts_paginated(user_id=1))
    assert len(pages) == 3
    assert pages == [
        PDAccountPage(
            results=[
                PDAccount(account_name="business", number="1234"),
                PDAccount(account_name="expense", number="2345"),
            ],
            page=1,
            next_page=2,
        ),
        PDAccountPage(
            results=[
                PDAccount(account_name="fun", number="6544"),
                PDAccount(account_name="holiday", number="9283"),
            ],
            page=2,
            next_page=3,
        ),
        PDAccountPage(
            results=[
                PDAccount(account_name="gifts", number="7827"),
                PDAccount(account_name="home", number="1259"),
            ],
            page=3,
            next_page=None,
        ),
    ]

    # Fails to connect when connecting to non-existent url.
    with pytest.raises(UnexpectedError) as exc_info:
        client.get("mock://testserver")
    assert str(exc_info.value) == "Error when contacting 'mock://testserver'"


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
