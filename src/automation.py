import logging
from hass_ae.components import Light, Outlet, TFSwitch, Switch
from hass_ae.components import InputBoolean, TFMotionSensor
from hass_ae.components import Vacuum
from hass_ae.handlers import TFMotionSensorHandler, TFSwitchHandler
from hass_ae.handlers import BooleanStateChangedHandler
from hass_ae.components import Timer
import hass_ae.domain

import enum
import time
import asyncio
import random

logger = logging.getLogger(__name__)

async def setup(client, state_manager, registry, **kwargs):
    registry.register([

        Vacuum(
            identity='kitt',
            alias='kitt',
            client=client,
            state_manager=state_manager
        ),

        # SWITCHES
        TFSwitch(
            identity='sw_tf_1',
            alias='livingroom',
            client=client,
            handler=LivingroomSwitchHandler(registry)
            ),

        TFSwitch(
            identity='sw_tf_3',
            alias='night',
            client=client,
            handler=NightSwitchHandler(registry)
        ),

        TFSwitch(
            identity='sw_tf_2',
            alias='secondary_entry',
            client=client,
            handler=SecondaryEntrySwitchHandler(registry)
        ),

        TFSwitch(
            identity='sw_tf_5',
            alias='tvroom',
            client=client,
            handler=TvRoomSwitchHandler(registry)
        ),

        TFSwitch(
            identity='sw_tf_6',
            alias='linus',
            client=client,
            handler=LinusRoomSwitchHandler(registry)
        ),

        TFSwitch(
            identity='sw_tf_garden',
            alias='garden',
            client=client,
            handler=GardenSwitchHandler(registry)
        ),

        Switch(
            identity='irrigation_control_valve_1', 
            alias='valve_1',
            client=client,
            state_manager=state_manager
        ),

        Switch(
            identity='irrigation_control_valve_2', 
            alias='valve_2',
            client=client,
            state_manager=state_manager
        ),

        Switch(
            identity='irrigation_control_valve_3', 
            alias='valve_3',
            client=client,
            state_manager=state_manager
        ),

        # MOTION SENSORS
        TFMotionSensor(
            identity='s_ms_tf_1',
            alias='secondary_entry',
            client=client,
            handler=SecondaryEntryMotionSensorHandler(registry)
        ),

        TFMotionSensor(
            identity='s_ms_tf_2',
            alias='entry',
            client=client,
            handler=EntryMotionSensorHandler(registry)
        ),

        # INPUT BOOLEANS
        InputBoolean(
            identity='ib_is_sleep', 
            alias='is_sleep',
            client=client,
            state_manager=state_manager,
            handler=SleepInputHandler(registry)
        ),

        InputBoolean(
            identity='ib_is_home', 
            alias='is_home',
            client=client,
            state_manager=state_manager,
            handler=HomeInputHandler(registry)
        ),

        InputBoolean(
            identity='ib_disco', 
            alias='disco',
            client=client,
            state_manager=state_manager,
            handler=DiscoInputHandler(registry)
        ),


        # LIGHTS
        Light(
            identity='l_tf_1',
            alias='livingroom_side',
            client=client,
            state_manager=state_manager
        ),
        Light(
            identity='l_tf_2',
            alias='livingroom_roof',
            client=client,
            state_manager=state_manager
        ),
        Light(
            identity='l_tf_3',
            alias='entry_roof_1',
            client=client,
            state_manager=state_manager
        ),
        Light(
            identity='l_tf_4',
            alias='secondaryentry_roof',
            client=client,
            state_manager=state_manager
        ),
        Light(
            identity='l_tf_5',
            alias='entry_roof_2',
            client=client,
            state_manager=state_manager
        ),
        Light(
            identity='l_tf_6',
            alias='linus_roof',
            client=client,
            state_manager=state_manager
        ),
        Light(
            identity='l_tf_7',
            alias='livingroom_roof_2',
            client=client,
            state_manager=state_manager
        ),



        # OUTLETS
        Outlet(
            identity='o_rf_1',
            alias='tablelamp',
            client=client,
            state_manager=state_manager
        ),
        Outlet(
            identity='o_rf_2',
            alias='whisky',
            client=client,
            state_manager=state_manager
        ),
        Outlet(
            identity='o_rf_3',
            alias='tv',
            client=client,
            state_manager=state_manager
        ),
        Outlet(
            identity='o_rf_4',
            alias='entrylight',
            client=client,
            state_manager=state_manager
        ),
        Outlet(
            identity='o_rf_5',
            alias='na_1',
            client=client,
            state_manager=state_manager
        ),
        Outlet(
            identity='o_tf_1',
            alias='upstairs_nightlight',
            client=client,
            state_manager=state_manager
        ),
    ])


    await registry.subscribe_all()

class HomeInputHandler(BooleanStateChangedHandler):

    def __init__(self, registry):
        self.registry = registry

    async def on(self):
        pass
        # await set_entry_lights(self.registry, True)
        # await set_livingroom_lights(self.registry, True)
        # await set_tvroom_lights(self.registry, True)

    async def off(self):
        await self.registry.get(Light, 'secondaryentry_roof').turn_off()
        await set_entry_lights(self.registry, False)
        await set_livingroom_lights(self.registry, False)
        await set_tvroom_lights(self.registry, False)
        await self.registry.get(Outlet, 'tv').turn_off()

class SleepInputHandler(BooleanStateChangedHandler):

    def __init__(self, registry):
        self.registry = registry

    async def on(self):
        pass
        # await set_entry_lights(self.registry, False)
        # await set_livingroom_lights(self.registry, False)
        # await set_tvroom_lights(self.registry, False)
        # await self.registry.get(Outlet, 'tv').turn_off()
        # await self.registry.get(Outlet, 'upstairs_nightlight').turn_on()

    async def off(self):
        pass

class DiscoInputHandler(BooleanStateChangedHandler):

    def __init__(self, registry):
        self.registry = registry
        self.timer = Timer(self._disco, 0)

    async def on(self):
        await self.timer.restart()
        await self.registry.get(Light, 'livingroom_roof').turn_off()

    async def off(self):
        if self.timer:
            await self.timer.cancel()
        await self.registry.get(Light, 'livingroom_roof_2').turn_off()

    async def _disco(self):
        light = self.registry.get(Light, 'livingroom_roof_2')
        while True:
            color = [random.randint(0,255), random.randint(0,255), random.randint(0,255)]
            await light.turn_on(brightness=100, color=color)
            await asyncio.sleep(1)

class LinusRoomSwitchHandler(TFSwitchHandler):

    def state_generator(self):
        while True:
            yield 10
            yield 40
            yield 70
            yield 100

    def __init__(self, registry):
        self.registry = registry
        self.reset_states()

    def reset_states(self):
        self.states = self.state_generator()

    async def on(self):
        await self.registry.get(Light, 'linus_roof').turn_on(brightness=next(self.states))

    async def on_long(self):
        await self.registry.get(Light, 'linus_roof').turn_on(brightness=100)
        self.reset_states()

    async def off(self):
        await self.registry.get(Light, 'linus_roof').turn_off()
        self.reset_states()

    async def off_long(self):
        await self.registry.get(Light, 'linus_roof').turn_off()
        self.reset_states()


class LivingroomSwitchHandler(TFSwitchHandler):

    def __init__(self, registry):
        self.registry = registry

    async def on(self):
        await set_livingroom_lights(self.registry, True, 100)
        await set_entry_lights(self.registry, True, 100)

    async def on_long(self):
        await set_livingroom_lights(self.registry, True, 50)
        await set_entry_lights(self.registry, True, 50)

    async def off(self):
        await set_livingroom_lights(self.registry, False)
        await set_entry_lights(self.registry, False)

    async def off_long(self):
        await set_livingroom_lights(self.registry, False)
        await set_entry_lights(self.registry, False)

class NightSwitchHandler(TFSwitchHandler):

    def __init__(self, registry):
        self.registry = registry

    async def on(self):
        await self.registry.get(InputBoolean, 'is_home').turn_on()

        await set_livingroom_lights(self.registry, True, 100)
        await set_entry_lights(self.registry, True, 100)
        await set_tvroom_lights(self.registry, True, 100)
        await self.registry.get(Outlet, 'upstairs_nightlight').turn_off()

    async def on_long(self):
        await self.registry.get(InputBoolean, 'is_home').turn_on()

        await set_livingroom_lights(self.registry, True, 50)
        await set_entry_lights(self.registry, True, 50)
        await set_tvroom_lights(self.registry, True, 50)
        await self.registry.get(Outlet, 'upstairs_nightlight').turn_off()

    async def off(self):
        await set_entry_lights(self.registry, False)
        await set_livingroom_lights(self.registry, False)
        await set_tvroom_lights(self.registry, False)
        await self.registry.get(Outlet, 'tv').turn_off()
        await self.registry.get(Outlet, 'upstairs_nightlight').turn_on()

    async def off_long(self):
        await self.registry.get(InputBoolean, 'is_home').turn_off()

class SecondaryEntrySwitchHandler(TFSwitchHandler):

    def __init__(self, registry):
        self.registry = registry

    async def on(self):
        await self.registry.get(InputBoolean, 'is_home').turn_on()
        await self.registry.get(Light, 'secondaryentry_roof').turn_on()

    async def off(self):
        await self.registry.get(InputBoolean, 'is_home').turn_off()


class TvRoomSwitchHandler(TFSwitchHandler):

    def __init__(self, registry):
        self.registry = registry

    async def on(self):
        await set_tvroom_lights(self.registry, True, 100)

    async def on_long(self):
        await self.registry.get(Outlet, 'tv').turn_on()

    async def off(self):
        await set_tvroom_lights(self.registry, False)
        await self.registry.get(Outlet, 'tv').turn_off()

    async def off_long(self):
        await set_tvroom_lights(self.registry, False)
        await self.registry.get(Outlet, 'tv').turn_off()

class SecondaryEntryMotionSensorHandler(TFMotionSensorHandler):
    
    def __init__(self, registry):
        self.registry = registry
        self.timer = None

    async def on(self):
        await self.registry.get(Light, 'secondaryentry_roof').set_state(
            True, brightness=100, duration=15*60)


class EntryMotionSensorHandler(TFMotionSensorHandler):

    def __init__(self, registry):
        self.registry = registry
        self.timer = None

    async def on(self):

        is_home = self.registry.get(InputBoolean, 'is_home').state

        if not is_home:
            return

        lights = [
            self.registry.get(Light, 'entry_roof_1'),
            self.registry.get(Light, 'entry_roof_2'),
        ]

        for l in lights:
            if not l.state:
                await l.turn_on(brightness=100, duration=5*60)

class GardenSwitchHandler(TFSwitchHandler):

    def __init__(self, registry):
        self.registry = registry
        self.valve_states = None

    def _get_valves(self):
        return [
            self.registry.get(Switch, 'valve_1'),
            self.registry.get(Switch, 'valve_2'),
            self.registry.get(Switch, 'valve_3'),
        ]

    async def valve_state_generator(self):
        valves = self._get_valves()
        current_valve = None

        while True:
            for valve in valves:
                if current_valve is not None:
                    logger.info(f'Stoping valve {current_valve}')
                    await current_valve.turn_off()
                    pass
                logger.info(f'Starting valve {valve}')
                await valve.turn_on()
                current_valve = valve
                yield valve

    async def _reset_valve_states(self):
        self.valve_states = self.valve_state_generator()
        for valve in self._get_valves():
            logger.info(f'Stoping valve {valve}')
            await valve.turn_off()
    
    async def _next_valve_state(self):
        if not self.valve_states:
            await self._reset_valve_states()

        active_valve = await self.valve_states.__anext__()

    async def on(self):
        await self._next_valve_state()

    async def on_long(self):
        await self._reset_valve_states()

    async def off(self):
        await self.registry.get(Vacuum, 'kitt').start()

    async def off_long(self):
        await self.registry.get(Vacuum, 'kitt').stop()


async def set_livingroom_lights(registry, on=True, brightess=None):
    asyncio.gather(
        registry.get(Light, 'livingroom_roof').set_state(on, brightness=brightess),
        registry.get(Light, 'livingroom_roof_2').set_state(on, brightness=brightess, color=Light.Color.WARM_WHITE),
        registry.get(Light, 'livingroom_side').set_state(on, brightness=brightess),
        registry.get(Outlet, 'tablelamp').set_state(on)
    )


async def set_tvroom_lights(registry, on=True, brightess=None):
    await registry.get(Outlet, 'whisky').set_state(on)


async def set_entry_lights(registry, on=True, brightess=None):
    asyncio.gather(
        registry.get(Light, 'entry_roof_1').set_state(on, brightness=brightess),
        registry.get(Light, 'entry_roof_2').set_state(on, brightness=brightess),
        registry.get(Outlet, 'entrylight').set_state(on)
    )

async def set_secondaryentry_lights(registry, on=True, brightess=None):
    await registry.get(Light, 'secondaryentry_roof').set_state(on, brightness=brightess),