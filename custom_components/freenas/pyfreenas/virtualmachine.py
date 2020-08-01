import asyncio

from enum import Enum, unique
from typing import Any, Callable, TypeVar

TController = TypeVar('TController', bound='Controller')
TState = TypeVar('TState', bound='VirturalMachineState')


@unique
class VirturalMachineState(Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"

    @classmethod
    def fromValue(cls, value: str) -> TState:
        if value == cls.STOPPED.value:
            return cls.STOPPED
        if value == cls.RUNNING.value:
            return cls.RUNNING
        raise Exception(f"Unexpected virtural machine state '{value}'")


class VirturalMachine(object):
    def __init__(self, controller: TController, id: int) -> None:
        self._controller = controller
        self._id = id
        self._cached_state = self._state

    async def start(self, overcommit: bool = False) -> bool:
        """Starts a stopped virtural machine."""
        result = await self._controller._client.invoke_method(
            "vm.start",
            [
                self._id,
                {"overcommit": overcommit},
            ],
        )
        return result

    async def stop(self, force: bool = False) -> bool:
        """Stops a running virtural machine."""
        result = await self._controller._client.invoke_method(
            "vm.stop",
            [
                self._id,
                force,
            ],
        )
        if result:
            self._controller._state["vms"][self._id]["status"] = {
                "pid": None, "state": str(VirturalMachineState.STOPPED)}
        return result

    async def restart(self) -> bool:
        """Restarts a running virtural machine."""
        result = await self._controller._client.invoke_method(
            "vm.restart",
            [
                self._id,
            ],
        )
        return result

    @property
    def available(self) -> bool:
        """If the virtural machine exists on the server."""
        return self._id in self._controller._state["vms"]

    @property
    def description(self) -> str:
        """The description of the virtural machine."""
        if self.available:
            self._cached_state = self._state
            return self._state["description"]
        return self._cached_state["description"]

    @property
    def id(self) -> int:
        """The id of the virtural machine."""
        return self._id

    @property
    def name(self) -> str:
        """The name of the virtural machine."""
        if self.available:
            self._cached_state = self._state
            return self._state["name"]
        return self._cached_state["name"]

    @property
    def status(self) -> VirturalMachineState:
        """The status of the virtural machine."""
        assert self.available
        return VirturalMachineState.fromValue(self._state["status"]["state"])

    @property
    def _state(self) -> dict:
        """The state of the virtural machine, according to the Controller."""
        return self._controller._state["vms"][self._id]
