import asyncio
import websockets

from .virtualmachine import VirturalMachine
from .websockets_custom import freenas_auth_protocol_factory
from typing import Any, Callable, List, TypeVar

T = TypeVar('T', bound='Controller')


class Controller(object):
    @classmethod
    async def create(cls, host: str, password: str, username: str = 'root') -> T:
        self = Controller()
        self._client = await websockets.connect(f"ws://{host}/websocket", create_protocol=freenas_auth_protocol_factory(username, password))
        self._vms = {}
        return self

    async def refresh(self):
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
        self._vms = {value["id"]: value for value in vms}

    @property
    def vms(self) -> List[VirturalMachine]:
        """Returns a list of virtual machines on the host."""
        return [VirturalMachine(controller=self, id=id) for id in self._vms]
