import pprint
import enum
import logging
import abc
import asyncio
import hass_ae.domain
from hass_ae.handlers import BooleanStateChangedHandler
import sys, inspect

logger = logging.getLogger(__name__)

class ComponentRegistrySection():

    def __init__(self, class_):
        self.class_ = class_
        self.components = dict()

    def register(self, component):
        if component.alias in self.components.keys():
            raise KeyError('A component by that name is already registered')
        self.components[component.alias] = component

    def get(self, alias):
        component = self.components.get(alias)
        if not component:
            raise RuntimeError(
                f'A componenet of type {self.class_.__name__} by name {alias} could not be found')
        return component

class ComponentRegistry():

    def __init__(self, *args, **kwargs):
        self._reg = dict()
        self.sections = dict()
        
    def register(self, components):
        for component in components:
            key = type(component).__name__
            if not key in self.sections.keys():
                self.sections[key] = ComponentRegistrySection(type(component))
            self.sections[key].register(component)

    def get(self, type_, alias):
        return self.sections[type_.__name__].get(alias)

    async def subscribe_all(self):
        for k, s in self.sections.items():
            for k, c in s.components.items():
                try:
                    logger.debug(f'trying to subscribe {k}')
                    await c.subscribe()
                except TypeError:
                    logger.exception(
                        f'{k} failed to subscribe')


class Component(abc.ABC):

    DOMAIN = hass_ae.domain.UNDEFINED

    def __init__(self, identity, alias, client, *args, **kwargs):
        self.identity = identity
        self.alias = alias
        self.full_identity = f'{self.DOMAIN}.{self.identity}'
        self.client = client

    async def subscribe(self):
        logger.debug(f'Subription of {type(self).__name__}[{self.alias}] is a no-op')

    def __repr__(self):
        return f'{self.full_identity}|{self.alias}:'


class TFSwitch(Component):

    DOMAIN = hass_ae.domain.SWITCH

    class States(enum.Enum):
        on_long=1001
        on=1002
        on_release=1003
        off_long=2001
        off=2002
        off_release=2003

    def __init__(self, handler, **kwargs):
        super().__init__(**kwargs)
        self.handler = handler

    async def subscribe(self):
        await self.client.subscribe('deconz_event', self.evaluate)

    async def check_event(self, data):
        id_ = data['event']['data']['id']
        logger.debug(f'checking switch event for id {self.identity} with event id {id_}')
        if self.identity != id_:
            raise NotApplicableError(f'switch {self.identity} did not send this event. It was {id_}')
        logger.info(f'switch {self.identity}|{self.alias} is acting on event with id {id_}')
        return self.States(data['event']['data']['event'])

    async def evaluate(self, data, *args, **kwargs):
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


class TFMotionSensor(Component):

    DOMAIN = hass_ae.domain.BINARY_SENSOR

    def __init__(self, handler, **kwargs):
        super().__init__(**kwargs)
        self.handler = handler

    async def subscribe(self):
        await self.client.subscribe('state_changed', self.evaluate)


    async def check_event(self, data):
        event_identity = data['event']['data']['entity_id']
        if self.full_identity != event_identity:
            raise NotApplicableError(f'motion sensor {self.identity} did not send this event. It was {event_identity}')
        return bool(data['event']['data']['new_state']['state'] == 'on')

    async def evaluate(self, data, *args, **kwargs):
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

class BoolenStateEntity(Component):

    DOMAIN = hass_ae.domain.UNDEFINED

    def __init__(self, state_manager, handler=None,  **kwargs):
        self.handler = handler
        self.state_manager = state_manager
        super().__init__(**kwargs)

    async def set_state(self, state:bool=True):
        if state:
            await self.turn_on()
        else:
            await self.turn_off()

    async def turn_on(self):
        logger.info(f'Turning on {self.full_identity}|{self.alias}')
        await self.client.call_service(
            domain=self.DOMAIN,
            service='turn_on',
            data={"service_data": {"entity_id": self.full_identity}})

    async def turn_off(self):
        logger.info(f'Turning off {self.full_identity}|{self.alias}')
        await self.client.call_service(
            domain=self.DOMAIN,
            service='turn_off',
            data={"service_data": {"entity_id": self.full_identity}})

    async def toggle(self):
        logger.info(f'Toggling {self.full_identity}|{self.alias}')
        await self.client.call_service(
            domain=self.DOMAIN,
            service='toggle',
            data={"service_data": {"entity_id": self.full_identity}})

    async def subscribe(self):
        """ Subscribe to state changes
        """

        logger.debug(f'Subription of {type(self).__name__}[{self.alias}]')

        async def _internal_handler(data):
            if self.state:
                await self.handler.on()
            else:
                await self.handler.off()
            return

        if self.handler:
            await self.state_manager.subscribe(self.full_identity, _internal_handler)

    @property
    def state(self):
        raw = self.state_manager.get(self.full_identity)
        return bool(raw.lower() == 'on')


class Light(BoolenStateEntity):

    DOMAIN = hass_ae.domain.LIGHT

    class Color:
        RED = [255, 0, 0]
        GREEN = [0, 255, 0]
        BLUE = [0, 0, 255]
        WHITE = [255, 255, 255]
        WARM_WHITE = [255, 226, 145]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.turn_off_timer = Timer(callback=self.turn_off, timeout=0)

    async def set_state(self, on=True, brightness=None, duration=None, color=None):
        if on:
            await self.turn_on(brightness, duration, color)
        else:
            await self.turn_off()

    async def turn_on(self, brightness=100, duration=None, color=None):
        logger.info(f'Turning on {self.full_identity}|{self.alias}|b:{brightness}')
        service_data = {"entity_id": self.full_identity}
        service_data.update({"transition": 0})
        if brightness:
            service_data.update({"brightness_pct": brightness})
        
        if color:
            service_data.update({"rgb_color": color})

        await self.client.call_service(
            domain=self.DOMAIN,
            service='turn_on',
            data={"service_data": service_data})

        if duration:
            self.turn_off_timer.timeout = duration
            await self.turn_off_timer.restart()
        else:
            await self.turn_off_timer.cancel()

    async def turn_off(self):
        logger.info(f'Turning off {self.full_identity}|{self.alias}')
        await self.turn_off_timer.cancel()

        service_data = {"entity_id": self.full_identity}
        service_data.update({"transition": 0})
        await self.client.call_service(
            domain=self.DOMAIN,
            service='turn_off',
            data={"service_data": service_data})


class Outlet(BoolenStateEntity):

    DOMAIN = hass_ae.domain.SWITCH

    async def set_state(self, on=True):
        if on:
            await self.turn_on()
        else:
            await self.turn_off()

class InputBoolean(BoolenStateEntity):
    DOMAIN = hass_ae.domain.INPUT_BOOLEAN


class Switch(BoolenStateEntity):
    DOMAIN = hass_ae.domain.SWITCH
    
class Vacuum(Component):

    DOMAIN = hass_ae.domain.VACUUM

    def __init__(self, state_manager, handler=None,  **kwargs):
        self.handler = handler
        self.state_manager = state_manager
        super().__init__(**kwargs)

    async def start(self):
        logger.info(f'Turning on {self.full_identity}|{self.alias}')
        await self.client.call_service(
            domain=self.DOMAIN,
            service='start',
            data={"service_data": {"entity_id": self.full_identity}})

    async def stop(self):
        logger.info(f'Returning {self.full_identity}|{self.alias}')
        await self.client.call_service(
            domain=self.DOMAIN,
            service='return_to_base',
            data={"service_data": {"entity_id": self.full_identity}})

    async def park(self):
        logger.info(f'Parking {self.full_identity}|{self.alias}')
        await self.client.call_service(
            domain=self.DOMAIN,
            service='stop',
            data={"service_data": {"entity_id": self.full_identity}})

    @property
    def state(self):
        raw = self.state_manager.get(self.full_identity)
        return bool(raw.lower() != 'docked')

class Timer():

    WEAKUP_INTERVAL = 60

    def __init__(self, callback, timeout):
        self.timeout = timeout
        self.callback = callback
        self.task = None
        self.time_left = timeout

    async def _timer_fn(self):

        def interval_generator():
            self.time_left = self.timeout
            while self.time_left > self.WEAKUP_INTERVAL:
                self.time_left = self.time_left-self.WEAKUP_INTERVAL
                yield self.WEAKUP_INTERVAL
            yield self.time_left

        for i in interval_generator():
            logger.debug(f'Timer: {self.time_left} remaining {self.callback}')
            await asyncio.sleep(i)

        logger.debug(f'Timer: executing {self.callback}')
        await self.callback()

    async def start(self):
        logger.debug(f'Timer: started {self.callback}')
        self.task = asyncio.create_task(self._timer_fn())

    async def restart(self):
        await self.cancel()
        await self.start()
    
    async def cancel(self):
        if self.task:
            logger.debug(f'Timer: canceled {self.callback}')
            self.task.cancel()

class Error(Exception):
    pass

class NotApplicableError(Error):
    pass