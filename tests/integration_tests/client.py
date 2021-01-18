from apiclient import APIClient, endpoint, paginated, retry_request


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
