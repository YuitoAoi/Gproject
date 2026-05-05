import abc
from typing import TypeVar
from msgspec import json, Struct

T = TypeVar("T")


class EntityBase[T](Struct):
    def to_json(self):
        return json.encode(self)

    @classmethod
    def from_json(cls, _str: str):
        return json.decode(_str, type=cls)
