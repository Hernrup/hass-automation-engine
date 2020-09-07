import enum
import logging

logger = logging.getLogger(__name__)

class Light():

    DOMAIN = 'light'

    def __init__(self, client, identity):
        self.identity = identity
        self.client = client
        self.full_identity = f'{self.DOMAIN}.{self.identity}'

    async def set_state(self, on=True, brightness=None):
        if on:
            await self.turn_on(brightness)
        else:
            await self.turn_off()

    async def turn_on(self, brightness=None):
        service_data = {"entity_id": self.full_identity}
        if brightness:
            service_data.update({"brightness_pct": brightness})

        await self.client.call_service(
            domain=self.DOMAIN,
            service='turn_on',
            data={"service_data": service_data})

    async def turn_off(self):
        await self.client.call_service(
            domain=self.DOMAIN,
            service='turn_off',
            data={"service_data": {"entity_id": self.full_identity}})

    async def toggle(self):
        await self.client.call_service(
            domain=self.DOMAIN,
            service='toggle',
            data={"service_data": {"entity_id": self.full_identity}})


class Outlet():

    DOMAIN = 'switch'

    def __init__(self, client, identity):
        self.identity = identity
        self.client = client
        self.full_identity = f'{self.DOMAIN}.{self.identity}'

    async def set_state(self, on=True):
        if on:
            await self.turn_on()
        else:
            await self.turn_off()

    async def turn_on(self):
        service_data = {"entity_id": self.full_identity}

        await self.client.call_service(
            domain=self.DOMAIN,
            service='turn_on',
            data={"service_data": service_data})

    async def turn_off(self):
        await self.client.call_service(
            domain=self.DOMAIN,
            service='turn_off',
            data={"service_data": {"entity_id": self.full_identity}})

    async def toggle(self):
        await self.client.call_service(
            domain=self.DOMAIN,
            service='toggle',
            data={"service_data": {"entity_id": self.full_identity}})


class TFSwitch():

    DOMAIN = 'switch'

    def __init__(self, client, identity, handler):
        self.identity = identity
        self.client = client
        self.full_identity = f'{self.DOMAIN}.{self.identity}'
        self.handler = handler

    async def check_event(self, data):
        id_ = data['event']['data']['id']
        logger.info(f'checking switch event for id {self.identity} with event id {id_}')
        if self.identity != id_:
            raise NotApplicableError(f'switch {self.identity} did not send this event. It was {id_}')
        logger.info(f'switch {self.identity} is acting on this event. It was {id_}')
        return TFSwitchState(data['event']['data']['event'])

    async def evaluate(self, data):
        try:
            signal = await self.check_event(data)
        except NotApplicableError:
            return

        

        signal_map = {
            TFSwitchState.on: self.handler.on,
            TFSwitchState.on_long: self.handler.on_long,
            TFSwitchState.on_release: self.handler.on_release,
            TFSwitchState.off: self.handler.off,
            TFSwitchState.off_long: self.handler.off_long,
            TFSwitchState.off_release: self.handler.off_release,

        }
        fn = signal_map.get(signal)
        return await fn(self.client)


class TFSwitchState(enum.Enum):
    on_long=1001
    on=1002
    on_release=1003
    off_long=2001
    off=2002
    off_release=2003

class TFSwitchHandler:

    @staticmethod
    async def on(client):
        pass

    @staticmethod
    async def on_long(client):
        pass

    @staticmethod
    async def on_release(client):
        pass

    @staticmethod
    async def off(client):
        pass

    @staticmethod
    async def off_long(client):
        pass

    @staticmethod
    async def off_release(client):
        pass
  
class Error(Exception):
    pass

class NotApplicableError(Error):
    pass


class TFMotionSensor():

    DOMAIN = 'binary_sensor'

    def __init__(self, client, identity, handler):
        self.identity = identity
        self.client = client
        self.full_identity = f'{self.DOMAIN}.{self.identity}'
        self.handler = handler

    async def check_event(self, data):
        event_identity = data['event']['data']['entity_id']
        if self.full_identity != event_identity:
            raise NotApplicableError(f'motion sensor {self.identity} did not send this event. It was {event_identity}')
        return bool(data['event']['data']['new_state']['state'] == 'on')

    async def evaluate(self, data):
        try:
            signal = await self.check_event(data)
        except NotApplicableError as e:
            print(str(e))
            return

        print(f'hej got signal {signal}')
        signal_map = {
            True: self.handler.on,
            False: self.handler.off,

        }
        fn = signal_map.get(signal)
        return await fn(self.client)

class TFMotionSensorHandler:

    @staticmethod
    async def on(client):
        pass

    @staticmethod
    async def off(client):
        pass