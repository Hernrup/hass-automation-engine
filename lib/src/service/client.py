#!/usr/bin/python3

import asyncio
import json
import websockets
import logging
import cachetools

logger = logging.getLogger(__name__)

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

    async def listen(self):
        while True:
            data = await self.ws.receive()
            # logger.info(data)
            if not data:
                break;
            try:
                await self.handle_event(data)
            except:
                logger.exception('Failure while handling event')

    async def authenticate(self, access_token):
        logger.info(f'Authenticating')
        await self.ws.send({'type': 'auth', 'access_token': access_token})

    async def subscribe(self, event_type, handler):
        identity = next(self.identity)
        self.subscriptions[identity] = handler
        logger.info(f'Subscribing to: {event_type} with identity {identity}')
        self.calls[identity] = f'Subscribing to: {event_type} with identity {identity}'
        await self.ws.send({'type': 'subscribe_events', 'event_type': event_type, 'id': identity})

    async def call_service(self, domain, service, data={}):
        identity = next(self.identity)
        logger.info(f'Calling service: {domain}.{service} with identity {identity}')
        identity = next(self.identity)
        res = {
            "type": "call_service",
            "domain": domain,
            "service": service,
            'id': identity
        }
        res.update(data)
        self.calls[identity] = f'Calling service: {domain}.{service} with identity {identity}'
        await self.ws.send(res)


    async def handle_event(self, data):
        try:
            identity = int(data['id'])
        except KeyError:
            return
        except TypeError:
            return

        if data['type'] == 'result':
            return self.result_handler(data)

        try:
            handler = self.subscriptions[identity]
        except KeyError:
            logger.error(f'No handler for subscription with id: {identity}')
            return

        return await handler(data, self)

            
    def result_handler(self, data):

        try:
            info = self.calls[data['id']]
            if data['success'] == True:
                logger.info(f'Successfull execution of {data["id"]} - {info}')
            else:
                logger.info(f'Failure in execution of {data["id"]} - {info}')
        except KeyError:
            logger.warning('No call registered for this result')
            if data['success'] == True:
                logger.info(data)
            else:
                logger.info(data)


def identity():
    """Identity value generator

    Used by client to generate a unique id for each message
    """
    id_ = 2
    while True:
        yield id_
        id_ = id_+2