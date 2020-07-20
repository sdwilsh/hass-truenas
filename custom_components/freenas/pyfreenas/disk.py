import asyncio

from enum import Enum, unique
from typing import Any, Callable, TypeVar

TController = TypeVar("TController", bound="Controller")
TType = TypeVar("TType", bound="DiskType")

@unique
class DiskType(Enum):
    HDD = "HDD"
    SSD = "SSD"

    @classmethod
    def fromValue(cls, value: str) -> TType:
        if value == str(cls.HDD):
            return cls.HDD
        if value == str(cls.SSD):
            return cls.SSD
        raise Exception(f"Unexpected disk type '{value}'")

class Disk(object):
    def __init__(self, controller: TController, name: str) -> None:
        self._controller = controller
        self._name = name

    @property
    def description(self) -> str:
        """The description of the desk."""
        return self._state["description"]

    @property
    def model(self) -> str:
        """The model of the disk."""
        return self._state["model"]

    @property
    def name(self) -> str:
        """The name of the disk."""
        return self._state["name"]

    @property
    def serial(self) -> str:
        """The serial of the disk."""
        return self._state["serial"]

    @property
    def size(self) -> int:
        """The size of the disk."""
        return self._state["size"]

    @property
    def temperature(self) -> int:
        """The temperature of the disk."""
        return self._state["temperature"]

    @property
    def type(self) -> DiskType:
        """The type of the desk."""
        return DiskType.fromValue(self._state["type"])

    @property
    def _state(self) -> dict:
        """The state of the desk, according to the Controller."""
        return self._controller._state["disks"][self._name]
