from dataclasses import dataclass
from typing import List, Optional

from jsonmarshal import json_field

from apiclient import APIClient, endpoint, paginated, retry_request, unmarshal_response


def by_query_params_callable(response, prev_params):
    if "nextPage" in response and response["nextPage"]:
        return {"page": response["nextPage"]}


@endpoint(base_url="http://testserver")
class Urls:
    users = "users"
    user = "users/{id}"
    accounts = "accounts"


class Client(APIClient):
    def get_request_timeout(self):
        return 0.1

    def list_users(self):
        return self.get(Urls.users)

    @retry_request
    def get_user(self, user_id: int):
        url = Urls.user.format(id=user_id)
        return self.get(url)

    def create_user(self, first_name, last_name):
        data = {"firstName": first_name, "lastName": last_name}
        return self.post(Urls.users, data=data)

    def overwrite_user(self, user_id, first_name, last_name):
        data = {"firstName": first_name, "lastName": last_name}
        url = Urls.user.format(id=user_id)
        return self.put(url, data=data)

    def update_user(self, user_id, first_name=None, last_name=None):
        data = {}
        if first_name:
            data["firstName"] = first_name
        if last_name:
            data["lastName"] = last_name
        url = Urls.user.format(id=user_id)
        return self.patch(url, data=data)

    def delete_user(self, user_id):
        url = Urls.user.format(id=user_id)
        return self.delete(url)

    @paginated(by_query_params=by_query_params_callable)
    def list_user_accounts_paginated(self, user_id):
        return self.get(Urls.accounts, params={"userId": user_id})


@dataclass
class User:
    user_id: int = json_field(json="userId")
    first_name: str = json_field(json="firstName")
    last_name: str = json_field(json="lastName")


@dataclass
class Account:
    account_name: str = json_field(json="accountName")
    number: str = json_field(json="number")


@dataclass
class AccountPage:
    results: List[Account] = json_field(json="results")
    page: int = json_field(json="page")
    next_page: Optional[int] = json_field(json="nextPage")


class ClientWithJson(Client):
    @unmarshal_response(List[User])
    def list_users(self):
        return super().list_users()

    @unmarshal_response(User)
    def get_user(self, user_id: int):
        return super().get_user(user_id)

    @unmarshal_response(User)
    def create_user(self, first_name, last_name):
        return super().create_user(first_name, last_name)

    @unmarshal_response(User)
    def overwrite_user(self, user_id, first_name, last_name):
        return super().overwrite_user(user_id, first_name, last_name)

    @unmarshal_response(User)
    def update_user(self, user_id, first_name=None, last_name=None):
        return super().update_user(user_id, first_name, last_name)

    def delete_user(self, user_id):
        return super().delete_user(user_id)

    @unmarshal_response(List[AccountPage])
    @paginated(by_query_params=by_query_params_callable)
    def list_user_accounts_paginated(self, user_id):
        return self.get(Urls.accounts, params={"userId": user_id})
