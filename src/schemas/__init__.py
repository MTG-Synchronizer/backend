from uuid import UUID
from typing import Any
from pydantic import AnyHttpUrl


class UUID4str(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: Any, field: Any) -> str:
        # Validate that the value is a valid UUID4
        try:
            uuid_obj = UUID(value, version=4)
        except ValueError:
            raise ValueError(f"'{value}' is not a valid UUID4")
        return str(uuid_obj)
    

class URLstr(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: Any, field: Any) -> str:
        # Validate that the value is a valid AnyHttpUrl
        try:
            url_obj = AnyHttpUrl(value)
        except ValueError:
            raise ValueError(f"'{value}' is not a valid URL")
        return str(url_obj)