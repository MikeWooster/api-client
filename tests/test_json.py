from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import List, Optional

import pytest
from jsonmarshal import json_field
from pydantic import BaseModel, Field

from apiclient import APIClient, marshal_request, serialize, serialize_all_methods, unmarshal_response


@dataclass
class Address:
    house_number: str = json_field(json="houseNumber")
    post_code: str = json_field(json="postCode")
    street: Optional[str] = json_field(json="street", omitempty=True)


@dataclass
class AccountHolder:
    first_name: str = json_field(json="firstName")
    last_name: str = json_field(json="lastName")
    middle_names: Optional[List[str]] = json_field(json="middleNames", omitempty=True)
    address: Address = json_field(json="address")
    date_of_birth: date = json_field(json="dob")


class AccountType(Enum):
    SAVING = "SAVING"
    CURRENT = "CURRENT"
    ISA = "ISA"


@dataclass
class Account:
    account_number: int = json_field(json="accountNumber")
    sort_code: int = json_field(json="sortCode")
    account_type: AccountType = json_field(json="accountType")
    account_holder: AccountHolder = json_field(json="accountHolder")
    date_opened: datetime = json_field(json="dateOpened")


class PDAddress(BaseModel):
    house_number: str = Field(alias="houseNumber")
    post_code: str = Field(alias="postCode")
    street: Optional[str]

    class Config:
        allow_population_by_field_name = True


class PDAccountHolder(BaseModel):
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    middle_names: Optional[List[str]] = Field(alias="middleNames")
    address: PDAddress
    date_of_birth: date = Field(alias="dob")

    class Config:
        allow_population_by_field_name = True


class PDAccount(BaseModel):
    account_number: int = Field(alias="accountNumber")
    sort_code: int = Field(alias="sortCode")
    account_type: AccountType = Field(alias="accountType")
    account_holder: PDAccountHolder = Field(alias="accountHolder")
    date_opened: datetime = Field(alias="dateOpened")

    class Config:
        allow_population_by_field_name = True


@pytest.fixture
def unserialized():
    return {
        "accountHolder": {
            "address": {"houseNumber": "12B", "postCode": "SW11 1AP"},
            "dob": "1980-02-28",
            "firstName": "John",
            "lastName": "Smith",
        },
        "account_number": 12345678,
        "accountType": "SAVING",
        "sortCode": 989898,
        "dateOpened": "2020-11-03T12:32:12",
    }


@pytest.fixture
def serialized(unserialized):
    return PDAccount(**unserialized)


@pytest.fixture
def unmarshalled():
    return Account(
        account_number=12345678,
        sort_code=989898,
        account_type=AccountType.SAVING,
        date_opened=datetime(2020, 11, 3, 12, 32, 12),
        account_holder=AccountHolder(
            first_name="John",
            last_name="Smith",
            middle_names=None,
            date_of_birth=date(1980, 2, 28),
            address=Address(house_number="12B", post_code="SW11 1AP", street=None),
        ),
    )


@pytest.fixture
def marshalled():
    return {
        "accountHolder": {
            "address": {"houseNumber": "12B", "postCode": "SW11 1AP"},
            "dob": "1980-02-28",
            "firstName": "John",
            "lastName": "Smith",
        },
        "accountNumber": 12345678,
        "accountType": "SAVING",
        "sortCode": 989898,
        "dateOpened": "2020-11-03T12:32:12",
    }


def test_marshal_request(unmarshalled, marshalled):
    @marshal_request()
    def decorated_func(endpoint: str, data: Account):
        return data

    got = decorated_func("", unmarshalled)
    assert got == marshalled


def test_unmarshal_response(unmarshalled, marshalled):
    @unmarshal_response(Account)
    def decorated_func():
        return marshalled

    got = decorated_func()
    assert got == unmarshalled


def test_marshal_request_with_time_fmts(unmarshalled, marshalled):
    @marshal_request(date_fmt="%d %B %y", datetime_fmt="%d %B %y %I %M %p")
    def decorated_func(endpoint: str, data: Account):
        return data

    got = decorated_func("", unmarshalled)

    marshalled["dateOpened"] = "03 November 20 12 32 PM"
    marshalled["accountHolder"]["dob"] = "28 February 80"
    assert got == marshalled


def test_unmarshal_request_with_time_fmts(unmarshalled, marshalled):
    @unmarshal_response(Account, date_fmt="%d %B %y", datetime_fmt="%d %B %y %I %M %S %p")
    def decorated_func():
        marshalled["dateOpened"] = "03 November 20 12 32 12 PM"
        marshalled["accountHolder"]["dob"] = "28 February 80"
        return marshalled

    got = decorated_func()

    assert got == unmarshalled


def test_serialize_request(unserialized, serialized):
    @serialize()
    def decorated_func(endpoint: str, data: PDAccount):
        return data

    @serialize()
    def decorated_func_args(endpoint: str, custom: str, data: PDAccount):
        return custom

    @serialize(PDAccount)
    def decorated_func_schema(endpoint: str, data):
        return data

    @serialize()
    def decorated_func_no_schema(endpoint: str, **kwargs):
        return kwargs  # data as is

    got = decorated_func("", "test", **unserialized)
    assert got == serialized.dict(by_alias=True, exclude_none=True)

    text = decorated_func_args("", custom="test", **unserialized)
    assert text == "test"

    got = decorated_func_schema("", **unserialized)
    assert got == serialized.dict(by_alias=True, exclude_none=True)

    got = decorated_func_no_schema("", **unserialized)
    assert got == unserialized


def test_serialize_response(unserialized, serialized):
    @serialize()
    def decorated_func(endpoint: str) -> PDAccount:
        return unserialized

    got = decorated_func("")
    assert got == serialized


def test_serialize_all_methods(unserialized, serialized):
    @serialize_all_methods()
    class MyApiClient(APIClient):
        def decorated_func(endpoint: str, data: PDAccount) -> PDAccount:
            return data

        def decorated_func_holder(endpoint: str, data: PDAccountHolder) -> PDAccountHolder:
            return data

    client = MyApiClient()

    got = client.decorated_func("", **unserialized)
    assert got == serialized

    got = client.decorated_func_holder("", **unserialized.get("accountHolder"))
    assert got == serialized.account_holder
