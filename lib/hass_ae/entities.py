import pprint
import enum
import logging
import abc

logger = logging.getLogger(__name__)

class InputSelect():

    DOMAIN = 'input_select'

    class States(enum.Enum):
        sleep = 1
        home = 2
        away = 3

    def __init__(self, identity, client, state_manager):
        self.identity = identity
        self.full_identity = f'{self.DOMAIN}.{self.identity}'
        self.state_manager = state_manager

    @property
    def state(self):
        raw = self.state_manager.get(self.full_identity)
        return self.States[raw.lower()]

class InputBoolean():

    DOMAIN = 'input_boolean'

    def __init__(self, identity, client, state_manager):
        self.identity = identity
        self.full_identity = f'{self.DOMAIN}.{self.identity}'
        self.state_manager = state_manager

    @property
    def state(self):
        raw = self.state_manager.get(self.full_identity)
        return bool(raw.lower() == 'on')


class Listner():

    def __init__(self, client, event):
        self.client = client
        self.event = event

    async def subscribe(self):
        await self.client.subscribe(self.event, self._callback_wrapper)
        
    async def _callback_wrapper(self, data, client):
        await self.callback(data)

    @abc.abstractmethod 
    async def callback(self, data):
        raise NotImplementedError()

class TFSwitch(Listner):

    DOMAIN = 'switch'

    class States(enum.Enum):
        on_long=1001
        on=1002
        on_release=1003
        off_long=2001
        off=2002
        off_release=2003

    def __init__(self, identity, client, handler):
        self.identity = identity
        self.client = client
        self.full_identity = f'{self.DOMAIN}.{self.identity}'
        self.handler = handler
        super().__init__(client, 'deconz_event')

    async def callback(self, data):
        await self.evaluate(data)

    async def check_event(self, data):
        id_ = data['event']['data']['id']
        logger.info(f'checking switch event for id {self.identity} with event id {id_}')
        if self.identity != id_:
            raise NotApplicableError(f'switch {self.identity} did not send this event. It was {id_}')
        logger.info(f'switch {self.identity} is acting on this event. It was {id_}')
        return self.States(data['event']['data']['event'])

    async def evaluate(self, data):
        try:
            signal = await self.check_event(data)
        except NotApplicableError:
            return

        signal_map = {
            self.States.on: self.handler.on,
            self.States.on_long: self.handler.on_long,
            self.States.on_release: self.handler.on_release,
            self.States.off: self.handler.off,
            self.States.off_long: self.handler.off_long,
            self.States.off_release: self.handler.off_release,

        }
        fn = signal_map.get(signal)
        return await fn()


class TFSwitchHandler(abc.ABC):

    async def on(self):
        pass

    async def on_long(self):
        pass

    async def on_release(self):
        pass

    async def off(self):
        pass

    async def off_long(self):
        pass

    async def off_release(self):
        pass
  

class TFMotionSensor(Listner):

    DOMAIN = 'binary_sensor'

    def __init__(self, client, identity, handler):
        self.identity = identity
        self.client = client
        self.full_identity = f'{self.DOMAIN}.{self.identity}'
        self.handler = handler
        super().__init__(client, 'state_changed')

    async def callback(self, data):
        await self.evaluate(data)

    async def check_event(self, data):
        event_identity = data['event']['data']['entity_id']
        if self.full_identity != event_identity:
            raise NotApplicableError(f'motion sensor {self.identity} did not send this event. It was {event_identity}')
        return bool(data['event']['data']['new_state']['state'] == 'on')

    async def evaluate(self, data):
        try:
            signal = await self.check_event(data)
        except NotApplicableError as e:
            return

        signal_map = {
            True: self.handler.on,
            False: self.handler.off,

        }
        fn = signal_map.get(signal)
        return await fn()

class TFMotionSensorHandler(abc.ABC):

    async def on(self):
        pass

    async def off(self):
        pass

class Error(Exception):
    pass

class NotApplicableError(Error):
    pass

