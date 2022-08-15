import asyncio

import pytest

from apiclient import JsonRequestFormatter, JsonResponseHandler, NoAuthentication
from apiclient.exceptions import UnexpectedError
from tests.integration_tests.client import AsyncClient, Urls


@pytest.mark.asyncio
async def test_client_response(mock_aioresponse):
    mock_aioresponse.get(
        Urls.users,
        status=200,
        payload=[
            {"userId": 1, "firstName": "Mike", "lastName": "Foo"},
            {"userId": 2, "firstName": "Sarah", "lastName": "Bar"},
            {"userId": 3, "firstName": "Barry", "lastName": "Baz"},
        ],
    )
    mock_aioresponse.post(
        Urls.users, status=201, payload={"userId": 4, "firstName": "Lucy", "lastName": "Qux"}
    )
    mock_aioresponse.put(
        Urls.user.format(id=4), status=200, payload={"userId": 4, "firstName": "Lucy", "lastName": "Foo"}
    )
    mock_aioresponse.patch(
        Urls.user.format(id=4), status=200, payload={"userId": 4, "firstName": "Lucy", "lastName": "Qux"}
    )
    mock_aioresponse.delete(Urls.user.format(id=4), status=204, payload=None)

    async with AsyncClient(
        authentication_method=NoAuthentication(),
        response_handler=JsonResponseHandler,
        request_formatter=JsonRequestFormatter,
    ) as client:
        responses = await asyncio.gather(
            client.list_users(),
            client.create_user(first_name="Lucy", last_name="Qux"),
            client.overwrite_user(user_id=4, first_name="Lucy", last_name="Foo"),
            client.update_user(user_id=4, first_name="Lucy", last_name="Qux"),
            client.delete_user(user_id=4),
            client.get("mock://testserver"),
            return_exceptions=True,
        )
        # users = await client.list_users()
        # new_user = await client.create_user(first_name="Lucy", last_name="Qux")
        # overwritten_user = await client.overwrite_user(user_id=4, first_name="Lucy", last_name="Foo")
        # updated_user = await client.update_user(user_id=4, first_name="Lucy", last_name="Qux")
        # deleted_user = await client.delete_user(user_id=4)
        users, new_user, overwritten_user, updated_user, deleted_user, error = responses

    assert len(users) == 3
    assert users == [
        {"userId": 1, "firstName": "Mike", "lastName": "Foo"},
        {"userId": 2, "firstName": "Sarah", "lastName": "Bar"},
        {"userId": 3, "firstName": "Barry", "lastName": "Baz"},
    ]

    assert new_user == {"userId": 4, "firstName": "Lucy", "lastName": "Qux"}
    assert overwritten_user == {"userId": 4, "firstName": "Lucy", "lastName": "Foo"}
    assert updated_user == {"userId": 4, "firstName": "Lucy", "lastName": "Qux"}
    assert deleted_user is None

    assert isinstance(error, UnexpectedError)
    with pytest.raises(UnexpectedError) as exc_info:
        async with AsyncClient() as client:
            await client.get("mock://testserver")
    assert str(exc_info.value) == "Error when contacting 'mock://testserver'"
