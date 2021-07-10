#!/usr/bin/python3

import asyncio
import json
import websockets
import logging
import cachetools
import enum
from collections import defaultdict

logger = logging.getLogger(__name__)

class ReservedIdentities(enum.Enum):
    AUTH = -1

class Websocket:
    """Class for managing a websocket connection

    This implementation must not contain any api-specific
    logic.
    """

    def __init__(self):
        self.socket = None

    async def connect(self, host, port):
        url = f'ws://{host}:{port}/api/websocket'
        logger.info(f'Connecting on {url}')
        self.socket = await websockets.connect(url)

    async def close(self):
        await self.socket.close()

    async def send(self, data):
        logger.debug(f'sending: {data}')
        if not data:
            raise ValueError('data is empty')
        await self._send_raw(json.dumps(data))

    async def receive(self):
        try:
            message = await self.socket.recv()
            message = json.loads(message)
            return message
        except:
            logger.exception('Failed to recieve event')
            raise

    async def _send_raw(self, message):
        try:
            await self.socket.send(message)
        except:
            logger.exception(f'Failed to send event: {message}')
            raise

class Client:
    """Class containing high level service functions for
    integration with Home Assistant websocket

    Uses a websocket instance
    """
    def __init__(self, websocket):
        self.ws = websocket
        self.identity = identity()
        self.subscriptions = {}
        self.calls = cachetools.TTLCache(maxsize=101, ttl=360)

    async def connect(self, host='localhost', port='8124'):
        await self.ws.connect(host, port)

    async def listen(self, blocking=True):

        async def _handle(data):
            try:
                await self.handle_event(data)
            except:
                logger.exception('Failure while handling event')
   
        logger.info('listner started')
        while True:
            data = await self.ws.receive()
            if not data:
                raise RuntimeError('no data, exiting')

            asyncio.create_task(_handle(data))

            if not blocking:
                break

        logger.info('listner terminated')


    async def authenticate(self, access_token):
        call = Call(
            identity=ReservedIdentities.AUTH.value,
            request={'type': 'auth', 'access_token': access_token},
            description=f'Authenticating'
            )
        await self.execute_call(call)
        await call.wait_for_complete()
        return call.data

    async def subscribe(self, event_type, handler):
        identity = next(self.identity)
        self.subscriptions[identity] = handler
        call = Call(
            identity=identity,
            request={'type': 'subscribe_events', 'event_type': event_type, 'id': identity},
            description=f'Subscribing to: {event_type} with handler {str(handler)}'
            )
        await self.execute_call(call)
        await call.wait_for_complete()
        return call.data

    async def call_service(self, domain, service, data={}):
        identity = next(self.identity)

        res = {
            "type": "call_service",
            "domain": domain,
            "service": service,
            'id': identity
        }
        res.update(data)

        call = Call(
            identity=identity,
            request=res,
            description=f'Calling service: {domain}.{service}'
            )

        await self.execute_call(call)
        await call.wait_for_complete()
        return call.data
    
    async def get_states(self):
        identity = next(self.identity)
        res = {
            "id": identity,
            "type": "get_states"
        }

        call = Call(
            identity=identity,
            request=res,
            description=f'Getting states'
            )
        await self.execute_call(call)
        await call.wait_for_complete()
        return call.data

    async def execute_call(self, call):
        logger.debug(f'Executing call [{call}]')
        self.calls[call.identity] = call
        await self.ws.send(call.request)


    async def handle_event(self, data):

        # check for auth event
        if data['type'] == 'auth_ok':
            return self.auth_handler(data)

        # check for result event
        if data['type'] == 'result':
            return self.result_handler(data)

        # check for custom handlers if event
        if data['type'] == 'event':
            try:
                identity = int(data['id'])
            except KeyError:
                logger.debug('event is missing id, discarding')
                return
            except TypeError:
                logger.debug('event is missing id, discarding')
                return

            try:
                handler = self.subscriptions[identity]
            except KeyError:
                logger.error(f'No handler for subscription with id: {identity}')
                return

            return await handler(data, self)
        
        # fallback
        return self.undefined_type_handler(data)

            
    def result_handler(self, data):
        try:
            call = self.calls[data['id']]
            if data['success'] == True:
                call.complete(data)
            else:
                call.fail(data)
        except KeyError:
            logger.warning(f'No call registered for result with id {data["id"]}')
            if data['success'] == True:
                logger.debug(data)
            else:
                logger.error(data)

    def auth_handler(self, data):

        if data['type'] == 'auth_ok':
            try:
                call = self.calls[ReservedIdentities.AUTH.value]
                call.complete(data)

            except KeyError:
                logger.warning(f'No call registered for authentication')

    def undefined_type_handler(self, data):
        logger.info(f'Unhandled datapackage: {data}')


def identity():
    """Identity value generator

    Used by client to generate a unique id for each message
    """
    id_ = 1
    while True:
        yield id_
        id_ = id_+1

class Call:

    def __init__(self, identity, request, description=''):
        self._is_complete = False
        self._is_ok = False
        self._request = request
        self._identity = identity
        self._response = None
        self._description = description

    @property
    def is_complete(self):
        return self._is_complete

    @property
    def is_ok(self):
        return self._is_ok

    @property
    def identity(self):
        return self._identity

    @property
    def request(self):
        return self._request

    @property
    def response(self):
        return self._response

    @property
    def data(self):
        return self._response.get('result')

    @property
    def description(self):
        return self._description

    def complete(self, payload):
        self._is_complete = True
        self._is_ok = True
        self._response = payload
        logger.debug(f'Completed call [{self}]')

    def fail(self, payload):
        self._is_complete = True
        self._is_ok = False
        self._response = payload
        logger.error(f'Failed call [{self}]')
        logger.error(f'Call {self.identity} - {self.description} failed, \n {self.request} \n {self.response}')

    async def wait_for_complete(self):
        while True:
            if self.is_complete:
                return
            await asyncio.sleep(0.1)

    
    def __repr__(self):
        return f'Call {self.identity} - {self.description}'

class StateManager():

    def __init__(self):
        self._states = dict()
        self._subscriptions = defaultdict(list)

    @property
    def states(self):
        return self._states
   
    def get(self, state, default=None):
        return self._states.get(state, default)

    async def update(self, state, value):
        self._states[state] = value
        logger.debug(f'{state} changed to {value}')
        await self._notify_subscribers(state, value)

    def load(self, data):
        self._states = self._parse_from_raw_states(data)

    @classmethod
    def _parse_from_raw_states(cls, data):
        return {d['entity_id']: d['state'] for d in data}

    async def subscribe(self, state, callback):
        self._subscriptions[state].append(callback)

    async def _notify_subscribers(self, state, data):
        for callback in self._subscriptions[state]:
            await callback(data)

    async def event_callback(self, data):
        await self.update(
            state=data['event']['data']['new_state']['entity_id'],
            value=data['event']['data']['new_state']['state']
            )
