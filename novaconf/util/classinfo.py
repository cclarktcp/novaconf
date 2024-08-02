"""utilities for analyzing python classes
"""

import dataclasses
from dataclasses import Field, is_dataclass, MISSING
from typing import Any
from types import MappingProxyType
from functools import cached_property


def is_missing(o: Any) -> bool:
    """check if object is a dataclass missing type

    Args:
        o (Any): any object to check

    Returns:
        bool: True if is a missing type else False
    """
    return o is MISSING or type(o) is MISSING

def field_has_default(field: Field) -> bool:
    """check if field has a default value

    Args:
        field (Field): dataclass Field object

    Returns:
        bool: True if field has a default value else False
    """
    return not is_missing(field.default) or not is_missing(field.default_factory)

def field_default_value(field: Field) -> Any:
    """get default value for field if available

    Args:
        field (Field): dataclass field object

    Returns:
        Any: default value if exists else dataclass.MISSING
    """
    if not is_missing(field.default):
        return field.default
    elif not is_missing(field.default_factory):
        return field.default_factory()

    return MISSING

    
class DataClassInfo:
    """DataClassInfo class"""

    def __init__(self, cls):
        """initializer for DataClassInfo

        Raises:
            TypeError: if `cls` is not a dataclass
        """
        if not is_dataclass(cls):
            raise TypeError(f"invalid type '{type(cls)}': `cls` must be a dataclass")

        self._cls = cls
        self._fieldmap = None

    @property
    def cls(self):
        return self._cls

    @cls.setter
    def cls(self, cls):
        """set class

        Args:
            cls (dataclass): dataclass class object
        """
        self._cls = cls
        del self.fields
        self._fieldmap = None

    @property
    def name(self) -> str:
        """return name of class

        Returns:
            str: name of the class
        """
        return self._cls.__name__

    @cached_property
    def fields(self) -> list[Field]:
        """return list of fields

        Returns:
            list[Field]: list of field descriptor objects
        """
        fields = dataclasses.fields(self.cls)
        fields = list(fields)
        self._fieldmap = {field.name: field for field in fields}
        return fields

    @property
    def fieldmap(self) -> dict[str, Field]:
        """return dict mapping field name to field descriptor

        Returns:
            dict[str, Field]: dict mapping field name to field
        """
        if "fields" not in self.__dict__:
            self.fields
        return self._fieldmap

    @property
    def required_fields(self) -> list[Field]:
        """get required fields (those with no default value)

        Returns:
            list[Field]: list of required fields
        """
        fields = list()
        for f in self.fields:
            if not field_has_default(f):
                fields.append(f)
            else:
                break
        return fields
    
    @property
    def optional_fields(self) -> list[Field]:
        """get optional fields (those with a default value)

        Returns:
            list[Field]: list of optional fields
        """
        fields = list()
        for f in self.fields[::-1]:
            if field_has_default(f):
                fields.append(f)
            else:
                break
        return fields[::-1]
    

    def get_field(self, field: str, default: Any = None) -> Field:
        """retrieve dataclass field descriptor object by its name

        Args:
            field (str): name of the field
            default (Any, optional): what to return when field is not present. Defaults to None.

        Returns:
            Field: dataclass field descriptor (if present)
            None: if `field` is not present
        """
        return self.fieldmap.get(field, default)

    def default_value(self, field: str) -> Any:
        """get default value for a field

        Args:
            field (str): field to get default for

        Raises:
            KeyError: if field does not exist

        Returns:
            Any: default value if it exists else dataclass.MISSING
        """
        fld = self.get_field(field)
        if fld is None:
            raise KeyError(f"{self.name} has no field '{field}'")

        return field_default_value(fld)
    
    def get_metadata(self, field: str) -> MappingProxyType:
        """get metadata for a field

        Args:
            field (str): field to get metadata for

        Raises:
            KeyError: if field does not exist

        Returns:
            mappingproxy: metadata for field
        """
        fld = self.get_field(field)
        if fld is None:
            raise KeyError(f"{self.name} has no field '{field}'")

        return fld.metadata


    def has_default(self, field: str) -> bool:
        """check if field has a default value

        Args:
            field (str): name of field

        Raises:
            KeyError: if field is not present

        Returns:
            bool: True if field has default else False
        """
        fld = self.get_field(field)
        if fld is None:
            raise KeyError(f"{self.name} has no field '{field}'")

        return field_has_default(fld)

    def split_required_optional_fields(self) -> tuple[list[Field], list[Field]]:
        """split fields into required and optional

        Returns:
            list[Field], list[Field]: tuple of two lists containing first required then optional fields
        """
        req, opt = list(), list()

        for field in self.fields:
            if field_has_default(field):
                opt.append(field)
            else:
                req.append(field)

        return req, opt
