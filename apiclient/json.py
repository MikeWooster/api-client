import dataclasses
from typing import Any, Dict, Generic, List, Optional, TypeVar

from apiclient.utils.typing import JsonType

T = TypeVar("T")


PRIMITIVES = {str, int, float}


def json_field(*args, json: str = None, metadata: dict = None, **kwargs):
    """Extend dataclass field with an additional json argument.

    This will allow the user to specify the format of the key in json.
    """
    if metadata is None:
        metadata = {}
    metadata["json"] = json
    return dataclasses.field(*args, metadata=metadata, **kwargs)


def marshall_response(schema: Generic[T]):
    """Decorator to marshall the response into the provided dataclass."""

    def decorator(func):
        def wrap(*args, **kwargs):
            response = func(*args, **kwargs)
            return response

        return wrap

    return decorator


class UnmarshalError(Exception):
    pass


class SchemaStart:
    pass


class SchemaEnd:
    pass


def unmarshal(response: JsonType, schema: Generic[T]) -> T:
    unmarshaller = _Unmarshaller(response, schema)
    return unmarshaller.unmarshal()
    # if _is_list(schema):
    #     if type(response) != list:
    #         raise MarshalError("Expecting response element to be an array: {elem}".format(elem=response))
    #     # The type of schema should be the first arg of the list
    #     inner_schema = schema.__args__[0]
    #
    #     return [unmarshal(e, inner_schema) for e in response]
    # else:
    #     return _unmarshall(response, schema)


@dataclasses.dataclass
class ResultContainer:
    data: JsonType
    schema: Any
    parent: Optional[str]
    cleaned: bool = False
    unmarshalled: bool = False

    @property
    def schema_type(self):
        # Return the primitive python type
        if self.schema in PRIMITIVES:
            return self.schema

        if dataclasses.is_dataclass(self.schema):
            return dict

        return self.schema.__origin__

    @property
    def item_type(self):
        return type(self.data)

    @property
    def inner_schema(self):
        return self.schema.__args__[0]

    @property
    def schema_fields(self):
        return self.schema.__dataclass_fields__

    @property
    def data_keys(self) -> List[str]:
        return list(self.data.keys())


class _Unmarshaller:
    def __init__(self, response, schema):
        self.result = [ResultContainer(data=response, schema=schema, parent=None)]
        self.dump = []

    def unmarshal(self):
        item = None
        while self.result:
            item = self.get_item()

            if len(self.result) == 0 and item.cleaned and item.unmarshalled:
                # If this is the first item and it has already been cleaned then we don't need to do anything
                continue

            if item.schema_type == list:
                self.process_list(item)

            elif item.schema_type == dict:
                self.process_dict(item)

            self.promote()

        if item is None:
            raise UnmarshalError("Unable to identify item structure")

        return item.data

    def get_item(self) -> ResultContainer:
        item = self.result.pop()
        self.validate_schema(item)
        return item

    @staticmethod
    def validate_schema(item: ResultContainer):
        if item.cleaned:
            return

        if item.item_type != item.schema_type:
            raise UnmarshalError(
                "Schema does not match type. schema = {schema}, data = {data}".format(
                    schema=item.schema, data=type(item.data)
                )
            )

    def process_list(self, item: ResultContainer):
        # Need to append to an intermediary list in order to preserve the final list order.
        rev = []
        while item.data:
            elem = item.data.pop()
            rev.append(ResultContainer(data=elem, schema=item.inner_schema, parent=item.parent))
        while rev:
            self.dump.append(rev.pop())

        # Put original (now empty item) back onto the result queue
        item.cleaned = True
        item.unmarshalled = True
        self.result.append(item)

    def process_dict(self, item: ResultContainer):
        if not item.cleaned:
            # Go through each known field and fix the keys in the original dictionary
            item = self.clean_item(item)

        if not self.dump:
            # This item has no children, we can safely unmarshal it to the specified datatype
            item.unmarshalled = True
            item.data = item.schema(**item.data)

        item.cleaned = True
        self.result.append(item)

    def clean_item(self, item: ResultContainer) -> ResultContainer:
        # Clean up the item (only called for dicts)
        for schema_key, field in item.schema_fields.items():
            json_key = get_json_key_for_item(field, item)

            if json_key == schema_key:
                # No need to do anything, it's already named correctly
                continue

            v = item.data.pop(json_key)
            # Put the data back under the expected schema key name
            item.data[schema_key] = v

        # Go through the data dict and remove any keys that are not defined in the schema
        for data_key in item.data_keys:
            if data_key not in item.schema_fields:
                item.data.pop(data_key)

        for data_key, v in item.data.items():
            schema_type = item.schema.__annotations__[data_key]
            if schema_type not in PRIMITIVES:
                self.dump.append(ResultContainer(data=v, schema=schema_type, parent=data_key))

        return item

    def promote(self):
        # promote combines the last element with it's parents.

        if self.dump:
            # If the dump contains items, then there is still stuff to process
            self.flush_dump()
            return

        while len(self.result) >= 2:
            item = self.result.pop()
            prev = self.result.pop()

            if item.cleaned is False:
                # This can happen when dealing with list of objects. we still need to unmarshall this data
                # putting both back on the result queue for processing and ending the promotion stage
                self.result.append(prev)
                self.result.append(item)
                break

            if prev.cleaned is False:
                # Previous item still needs processing
                self.dump.append(prev)
                self.result.append(item)
                continue

            if prev.schema_type == list:
                # At this point item should be fully unmarshalled so appending directly
                # to the prev list will be possible
                prev.data.append(item.data)
                self.result.append(prev)
                self.flush_dump()

            elif prev.schema_type == dict and item.parent in prev.data:
                # Put the object on the parents data key then back onto the result queue
                prev.data[item.parent] = item.data
                # prev has been updated so needs further processing
                self.result.append(prev)
            else:
                self.result.append(prev)
                self.dump.append(item)

        # Ensure that we haven't left anything in the dump
        self.flush_dump()

    def flush_dump(self):
        # Put all dumped items back onto the result queue
        while self.dump:
            self.result.append(self.dump.pop())


# def _unmarshall(response: Dict[str, JsonType], schema):
#     output = {}
#     for key, field in schema.__dataclass_fields__.items():
#
#         json_key = _determine_json_key(field)
#         if json_key not in response:
#             raise UnmarshalError(
#                 "Expected key '{key}' is not present in response: {response}".format(
#                     key=key, response=response
#                 )
#             )
#
#         value = response[json_key]
#         if value in (dict, list):
#             value = unmarshal()
#         output[key] = response[json_key]
#     breakpoint()
#     return schema()


def get_json_key_for_item(field: dataclasses.Field, item: ResultContainer) -> str:
    json_key = get_json_key(field)

    if json_key in item.data:
        return json_key

    if field.name in item.data:
        return field.name

    raise UnmarshalError(
        "Expected json key is not present in object. {key} not in {data}".format(
            key=json_key, data=item.data
        )
    )


def get_json_key(field: dataclasses.Field) -> str:
    if field.metadata.get("json"):
        # The field is defined, we can just use this.
        return field.metadata["json"]

    return field.name
