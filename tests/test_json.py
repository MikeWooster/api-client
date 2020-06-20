from dataclasses import dataclass
from typing import List, Optional

from apiclient.json import json_field, unmarshal


def test_marshal():
    @dataclass
    class Item:
        sub_key_1: int = json_field(json="subKey1")
        sub_key_2: float = json_field(json="subKey2")
        sub_key_3: str = json_field(json="subKey3")

    @dataclass
    class Obj:
        obj_key_1: str = json_field(json="objKey1")
        obj_key_2: int = json_field(json="objKey2")

    # Define the container as a dataclass
    @dataclass
    class Container:
        key: str
        meta_key: str = json_field(json="metaKey")
        array_key: List[str] = json_field(json="arrayKey")
        array_of_items: List[Item] = json_field(json="arrayOfItems")
        sub_object: Obj = json_field(json="subObject")

    json = {
        "key": "key-output",
        "metaKey": "meta-key-output",
        "arrayKey": ["elem1", "elem2", "elem3"],
        "arrayOfItems": [
            {"subKey1": 123, "subKey2": 123.99, "subKey3": "sub-key-3-output"},
            {"subKey1": 456, "subKey2": 456.99, "subKey3": "second-sub-key-3-output"},
        ],
        "subObject": {"objKey1": "obj-key-1-value", "objKey2": 951},
    }

    want = Container(
        key="key-output",
        meta_key="meta-key-output",
        array_key=["elem1", "elem2", "elem3"],
        array_of_items=[
            Item(sub_key_1=123, sub_key_2=123.99, sub_key_3="sub-key-3-output"),
            Item(sub_key_1=456, sub_key_2=456.99, sub_key_3="second-sub-key-3-output"),
        ],
        sub_object=Obj(obj_key_1="obj-key-1-value", obj_key_2=951),
    )
    got = unmarshal(json, Container)

    assert got == want


def test_iterable_json():
    @dataclass
    class Item:
        first_val: str = json_field(json="firstVal")
        second_val: int = json_field(json="secondVal")
        third_val: float = json_field(json="thirdVal")
        fourth_val: Optional[str] = json_field(json="fourthVal")

    json = [
        {"firstVal": "foo", "secondVal": 123, "thirdVal": 456.789, "fourthVal": None},
        {"firstVal": "bar", "secondVal": 654, "thirdVal": 555.241, "fourthVal": "pong"},
        {"firstVal": "baz", "secondVal": 987, "thirdVal": 111.324, "fourthVal": None},
    ]

    want = [
        Item(first_val="foo", second_val=123, third_val=456.789, fourth_val=None),
        Item(first_val="bar", second_val=654, third_val=555.241, fourth_val="pong"),
        Item(first_val="baz", second_val=987, third_val=111.324, fourth_val=None),
    ]

    got = unmarshal(json, List[Item])

    assert got == want


def test_simple_object():
    @dataclass
    class Item:
        first_val: str = json_field(json="firstVal")

    json = {"firstVal": "hello"}

    want = Item(first_val="hello")
    got = unmarshal(json, Item)
    assert got == want


def test_simple_object_with_fields_we_dont_care_about():
    @dataclass
    class Item:
        first_val: str = json_field(json="firstVal")

    json = {"firstVal": "hello", "secondVal": "there"}

    want = Item(first_val="hello")
    got = unmarshal(json, Item)
    assert got == want


def test_simple_array():
    json = ["elem1", "elem2", "elem3"]

    got = unmarshal(json, List[str])
    want = json
    assert got == want


def test_simple_array_with_simple_object():
    @dataclass
    class Item:
        first_val: str = json_field(json="firstVal")

    json = [{"firstVal": "hello", "secondVal": "there"}]

    want = [Item(first_val="hello")]
    got = unmarshal(json, List[Item])
    assert got == want


def test_simple_array_with_multiple_simple_objects():
    @dataclass
    class Item:
        first_val: str = json_field(json="firstVal")

    json = [
        {"firstVal": "hello", "secondVal": "there"},
        {"firstVal": "test", "secondVal": "there"},
        {"firstVal": "var", "secondVal": "there"},
    ]

    want = [Item(first_val="hello"), Item(first_val="test"), Item(first_val="var")]
    got = unmarshal(json, List[Item])

    assert got == want


def test_simple_nesting_of_objects():
    @dataclass
    class Item:
        first_val: str = json_field(json="firstVal")

    @dataclass
    class Parent:
        item: Item = json_field(json="item")

    json = {"item": {"firstVal": "hello"}}

    want = Parent(item=Item(first_val="hello"))
    got = unmarshal(json, Parent)

    assert got == want
