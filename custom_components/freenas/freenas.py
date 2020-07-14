import asyncio
import ejson
import functools
import logging
import uuid
import websockets

from typing import Any, Callable, TypeVar
from websockets.client import WebSocketClientProtocol


class FreeNASWebSocketClientProtocol(WebSocketClientProtocol):
    def __init__(self, *args, username: str, password: str, **kwargs):
        super().__init__(*args, **kwargs)
        self._username = username
        self._password = password
        self._method_lock = asyncio.Lock()

    async def handshake(self, *args, **kwargs):
        await WebSocketClientProtocol.handshake(self, *args, **kwargs)
        await self.send(ejson.dumps({
            'msg': 'connect',
            'version': '1',
            'support': ['1'],
        }))
        recv = ejson.loads(await self.recv())
        if recv['msg'] != 'connected':
            raise websockets.exceptions.NegotiationError('Unable to connect.')

        result = await self.invoke_method('auth.login', [self._username, self._password])
        if not result:
            raise websockets.exceptions.SecurityError(
                'Unable to authenticate.')
    
    async def invoke_method(self, method: str, params: [Any]) -> Any:
        async with self._method_lock:
            id = str(uuid.uuid4())
            await super().send(ejson.dumps({
                'id': id,
                'msg': 'method',
                'method': method,
                'params': params,
            }))
            recv = ejson.loads(await super().recv())
            if recv['id'] != id or recv['msg'] != 'result':
                raise websockets.exceptions.ProtocolError('Unexpected message')
            return recv['result']


def freenas_auth_protocol_factory(username: str, password: str) -> Callable[[Any], FreeNASWebSocketClientProtocol]:
    return functools.partial(FreeNASWebSocketClientProtocol, username=username, password=password)


T = TypeVar('T', bound='Controller')


class Controller(object):
    @classmethod
    async def create(cls, host: str, password: str, username: str = 'root') -> T:
        self = Controller()
        self._client_lock = asyncio.Lock()
        self._client = await websockets.connect(f"ws://{host}/websocket", create_protocol=freenas_auth_protocol_factory(username, password))
        return self

    async def refresh(self):
        pass
