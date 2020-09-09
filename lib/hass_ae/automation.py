import logging
from hass_ae.entities import Light
from hass_ae.entities import Outlet
from hass_ae.entities import TFSwitch, TFSwitchHandler
from hass_ae.entities import TFMotionSensor, TFMotionSensorHandler
from hass_ae.entities import InputBoolean
from hass_ae.entities import Timer
import enum
import time
import asyncio

logger = logging.getLogger(__name__)

class DEVICES:
    # lights
    light_livingroom_side='l_tf_1'
    light_livingroom_roof='l_tf_2'
    light_entry_roof_1='l_tf_3'
    light_secondaryentry_roof='l_tf_4'
    light_entry_roof_2='l_tf_5'
    # switches
    switch_entry='sw_tf_4'
    switch_livingroom='sw_tf_1'
    switch_secondary_entry='sw_tf_2'
    switch_tvroom='sw_tf_5'
    switch_night='sw_tf_3'
    #outlets
    outlet_whisky='o_rf_2'
    outlet_tablelamp_1='o_rf_1'
    outlet_tv='o_rf_3'
    outlet_na_1='o_rf_5'
    outlet_entrylight='o_rf_4'
    outlet_pc_room='o_tf_1'
    #sensors
    motionsensor_secondaryentry='s_ms_tf_1'
    motionsensor_entry='s_ms_tf_2'


async def setup(client, state_manager):

    await TFSwitch(
        identity=DEVICES.switch_livingroom,
        client=client,
        handler=LivingroomSwitchHandler(client)
    ).subscribe()

    await TFSwitch(
        identity=DEVICES.switch_night,
        client=client,
        handler=NightSwitchHandler(client, state_manager)
    ).subscribe()

    await TFSwitch(
        identity=DEVICES.switch_secondary_entry,
        client=client,
        handler=SecondaryEntrySwitchHandler(client, state_manager)
    ).subscribe()

    await TFSwitch(
        identity=DEVICES.switch_tvroom,
        client=client,
        handler=TvRoomSwitchHandler(client, state_manager)
    ).subscribe()

    await TFMotionSensor(
        identity=DEVICES.motionsensor_secondaryentry,
        client=client,
        handler=SecondaryEntryMotionSensorHandler(client, state_manager)
    ).subscribe()

    await TFMotionSensor(
        identity=DEVICES.motionsensor_entry,
        client=client,
        handler=EntryMotionSensorHandler(client, state_manager)
    ).subscribe()

class LivingroomSwitchHandler(TFSwitchHandler):

    def __init__(self, client):
        self.client = client

    async def on(self):
        await set_livingroom_lights(self.client, True, 100)
        await set_entry_lights(self.client, True, 100)

    async def on_long(self):
        await set_livingroom_lights(self.client, True, 30)
        await set_entry_lights(self.client, True, 30)

    async def off(self):
        await set_livingroom_lights(self.client, False)
        await set_entry_lights(self.client, False)

    async def off_long(self):
        await set_livingroom_lights(self.client, False)
        await set_entry_lights(self.client, False)

class NightSwitchHandler(TFSwitchHandler):

    def __init__(self, client, state_manager):
        self.client = client
        self.state_manager = state_manager

    async def on(self):
        await InputBoolean('ib_is_sleep', self.client, self.state_manager).turn_off()
        await InputBoolean('ib_is_home', self.client, self.state_manager).turn_on()

    async def off(self):
        await InputBoolean('ib_is_sleep', self.client, self.state_manager).turn_on()

        await set_entry_lights(self.client, self.state_manager, False)
        await set_livingroom_lights(self.client, self.state_manager, False)
        await set_tvroom_lights(self.client, self.state_manager, False)
        # await Outlet(self.client, DEVICES.outlet_tv).turn_off()

class SecondaryEntrySwitchHandler(TFSwitchHandler):

    def __init__(self, client, state_manager):
        self.client = client
        self.state_manager = state_manager

    async def on(self):
        await InputBoolean('ib_is_home', self.client, self.state_manager).turn_on()
        await InputBoolean('ib_is_sleep', self.client, self.state_manager).turn_off()

    async def off(self):
        await InputBoolean('ib_is_home', self.client, self.state_manager).turn_off()
        await InputBoolean('ib_is_sleep', self.client, self.state_manager).turn_off()

        await Light(DEVICES.light_secondaryentry_roof, self.client, self.state_manager).turn_off()
        await set_entry_lights(self.client, self.state_manager, False)
        await set_livingroom_lights(self.client, self.state_manager, False)
        await set_tvroom_lights(self.client, self.state_manager, False)
        # await Outlet(self.client, DEVICES.outlet_tv).turn_off()


class TvRoomSwitchHandler(TFSwitchHandler):

    def __init__(self, client, state_manager):
        self.client = client
        self.state_manager = state_manager

    async def on(self):
        await set_tvroom_lights(self.client, True, 100)
        await Outlet(DEVICES.outlet_tv, self.client, self.state_manager).turn_on()

    async def on_long(self):
        await set_tvroom_lights(self.client, self.state_manager, True, 30)

    async def off(self):
        await set_tvroom_lights(self.client, self.state_manager, False)

    async def off_long(self):
        await set_tvroom_lights(self.client, self.state_manager, False)
        await Outlet(DEVICES.outlet_tv, self.client, self.state_manager).turn_off()

class SecondaryEntryMotionSensorHandler(TFMotionSensorHandler):

    def __init__(self, client, state_manager):
        self.client = client
        self.state_manager = state_manager
        self.timer = None

    async def on(self):
        await Light(DEVICES.light_secondaryentry_roof, self.client, self.state_manager).set_state(True, brightness=100)

        async def timer_callback():
            await Light(DEVICES.light_secondaryentry_roof, self.client, self.state_manager).set_state(False)

        self.timer = Timer(callback=timer_callback, timeout=15*60) 
        await self.timer.restart()


class EntryMotionSensorHandler(TFMotionSensorHandler):

    def __init__(self, client, state_manager):
        self.client = client
        self.state_manager = state_manager
        self.timer = None

    async def on(self):

        is_home = InputBoolean('ib_is_home', self.client, self.state_manager).state
        is_sleep = InputBoolean('ib_is_sleep', self.client, self.state_manager).state
        
        logger.debug('Entry sensor triggered')

        async def _handle(l):
            if (is_sleep and is_home) or not is_home:
                logger.debug('Sleep or away mode active: turning on dimmed lights temporarely')
                brightess=20
                await l.turn_on(brightness=brightess)
                self.timer = Timer(callback=l.turn_off, timeout=5*60) 
                await self.timer.restart()
            else: 
                if not l.state:
                    logger.debug('Turning on dimmed entry lights')
                    await l.turn_on(brightness=50)
                else:
                    logger.debug('entry lights already on, no action')
        
        await _handle(Light(DEVICES.light_entry_roof_1, self.client, self.state_manager))
        await _handle(Light(DEVICES.light_livingroom_roof, self.client, self.state_manager))


async def set_livingroom_lights(client, state_manager, on=True, brightess=None):
    await Light(DEVICES.light_livingroom_roof, client, state_manager).set_state(on, brightness=brightess)
    await Light(DEVICES.light_livingroom_side, client, state_manager).set_state(on, brightness=brightess)
    await Outlet(DEVICES.outlet_tablelamp_1, client, state_manager).set_state(on)


async def set_tvroom_lights(client, state_manager, on=True, brightess=None):
    await Outlet(DEVICES.outlet_whisky, client, state_manager).set_state(on)


async def set_entry_lights(client, state_manager, on=True, brightess=None):
    await Light(DEVICES.light_entry_roof_1, client, state_manager).set_state(on, brightness=brightess)
    await Light(DEVICES.light_entry_roof_2, client, state_manager).set_state(on, brightness=brightess)
    await Outlet(DEVICES.outlet_entrylight, client, state_manager).set_state(on)


async def set_secondaryentry_lights(client, state_manager, on=True, brightess=None):
    await Light(DEVICES.light_secondaryentry_roof, client, state_manager).set_state(on, brightness=brightess)