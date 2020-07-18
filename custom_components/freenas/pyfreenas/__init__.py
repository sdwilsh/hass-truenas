import asyncio
import websockets

from .virtualmachine import VirturalMachine
from .websockets_custom import freenas_auth_protocol_factory
from typing import Any, Callable, Dict, List, TypeVar

T = TypeVar('T', bound='Controller')


class Controller(object):
    @classmethod
    async def create(cls, host: str, password: str, username: str = 'root') -> T:
        self = Controller()
        self._client = await websockets.connect(f"ws://{host}/websocket", create_protocol=freenas_auth_protocol_factory(username, password))
        self._state = None
        self._vms = None
        return self

    async def refresh(self) -> None:
        vms = await self._fetch_vms()
        self._state = {
            "vms": vms,
        }
        self._update_properties_from_state()

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
        self._vms = [VirturalMachine(
            controller=self, id=vm_id) for vm_id in self._state["vms"]]

    @property
    def vms(self) -> List[VirturalMachine]:
        """Returns a list of virtual machines on the host."""
        return self._vms
