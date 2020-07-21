import asyncio
import websockets

from .disk import Disk
from .virtualmachine import VirturalMachine
from .websockets_custom import FreeNASWebSocketClientProtocol, freenas_auth_protocol_factory
from typing import Any, Callable, Dict, List, TypeVar

T = TypeVar('T', bound='Controller')


class Controller(object):
    _client: FreeNASWebSocketClientProtocol

    @classmethod
    async def create(cls, host: str, password: str, username: str = 'root') -> T:
        self = Controller()
        self._client = await websockets.connect(f"ws://{host}/websocket", create_protocol=freenas_auth_protocol_factory(username, password))
        self._info = await self._client.invoke_method("system.info")
        self._state = None
        self._disks = None
        self._vms = None
        return self

    async def refresh(self) -> None:
        self._state = {
            "disks": await self._fetch_disks(),
            "vms": await self._fetch_vms(),
        }
        self._update_properties_from_state()

    async def _fetch_disks(self) -> Dict[str, dict]:
        disks = await self._client.invoke_method(
            "disk.query",
            [
                [],
                {
                    "select": [
                        "description",
                        "model",
                        "name",
                        "serial",
                        "size",
                        "type",
                    ],
                }
            ],
        )
        disks = {disk["name"]: disk for disk in disks}
        temps = await self._client.invoke_method(
            "disk.temperatures",
            [
                [disk for disk in disks],
            ],
        )
        for name, temp in temps.items():
            disks[name]['temperature'] = temp

        return disks

    async def _fetch_vms(self) -> Dict[str, dict]:
        vms = await self._client.invoke_method(
            'vm.query',
            [
                [],
                {
                    'select': [
                        'id',
                        'name',
                        'description',
                        'status',
                    ],
                },
            ],
        )
        return {vm["id"]: vm for vm in vms}

    def _update_properties_from_state(self) -> None:
        self._disks = [Disk(controller=self, name=disk_name)
                       for disk_name in self._state["disks"]]
        self._vms = [VirturalMachine(
            controller=self, id=vm_id) for vm_id in self._state["vms"]]

    @property
    def disks(self) -> List[Disk]:
        """Returns a list of disks attached to the host."""
        return self._disks

    @property
    def info(self) -> Dict[str, Any]:
        return self._info

    @property
    def vms(self) -> List[VirturalMachine]:
        """Returns a list of virtual machines on the host."""
        return self._vms
