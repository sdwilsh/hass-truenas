
import asyncio
import websockets

from .websockets_custom import freenas_auth_protocol_factory
from typing import Any, Callable, TypeVar

T = TypeVar('T', bound='Controller')


class Controller(object):
    @classmethod
    async def create(cls, host: str, password: str, username: str = 'root') -> T:
        self = Controller()
        self._client = await websockets.connect(f"ws://{host}/websocket", create_protocol=freenas_auth_protocol_factory(username, password))
        self._vms = []
        return self

    async def refresh(self):
        self._vms = await self._client.invoke_method(
            'vm.query',
            [
                [],
                {
                    'select': [
                        'id',
                        'name',
                        'description',
                        'state',
                    ],
                },
            ],
        )

    @property
    def vms(self):
        """Returns a list of virtual machines on the host."""
        return self._vms
