import logging
from hass_ae.dl import Light, TFSwitch, TFSwitchState, TFSwitchHandler
from hass_ae.dl import Outlet, TFMotionSensor, TFMotionSensorHandler
import hass_ae.dl
import hass_ae.entities
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
    ib_home = hass_ae.entities.InputBoolean('ib_is_home', client, state_manager)
    ib_sleep = hass_ae.entities.InputBoolean('ib_is_sleep', client, state_manager)

    await hass_ae.entities.TFSwitch(
        identity=DEVICES.switch_livingroom,
        client=client,
        handler=LivingroomSwitchHandler(client)
    ).subscribe()

    await hass_ae.entities.TFSwitch(
        identity=DEVICES.switch_night,
        client=client,
        handler=NightSwitchHandler(client)
    ).subscribe()

    await hass_ae.entities.TFSwitch(
        identity=DEVICES.switch_secondary_entry,
        client=client,
        handler=SecondaryEntrySwitchHandler(client)
    ).subscribe()

    await hass_ae.entities.TFSwitch(
        identity=DEVICES.switch_tvroom,
        client=client,
        handler=TvRoomSwitchHandler(client)
    ).subscribe()

    await hass_ae.entities.TFMotionSensor(
        identity=DEVICES.motionsensor_secondaryentry,
        client=client,
        handler=SecondaryEntryMotionSensorHandler(client)
    ).subscribe()


class LivingroomSwitchHandler(hass_ae.entities.TFSwitchHandler):

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

class NightSwitchHandler(hass_ae.entities.TFSwitchHandler):

    def __init__(self, client):
        self.client = client

    async def on(self):
        await set_entry_lights(self.client, True)
        await set_livingroom_lights(self.client, True)
        await set_tvroom_lights(self.client, True)

    async def off(self):
        await set_entry_lights(self.client, False)
        await set_livingroom_lights(self.client, False)
        await set_tvroom_lights(self.client, False)
        await Outlet(self.client, DEVICES.outlet_tv).turn_off()

class SecondaryEntrySwitchHandler(hass_ae.entities.TFSwitchHandler):

    def __init__(self, client):
        self.client = client

    async def on(self):
        await set_entry_lights(self.client, True)
        await set_livingroom_lights(self.client, True)
        await set_tvroom_lights(self.client, True)

    async def off(self):
        await set_entry_lights(self.client, False)
        await set_livingroom_lights(self.client, False)
        await set_tvroom_lights(self.client, False)
        await Outlet(self.client, DEVICES.outlet_tv).turn_off()


class TvRoomSwitchHandler(hass_ae.entities.TFSwitchHandler):

    def __init__(self, client):
        self.client = client

    async def on(self):
        await set_tvroom_lights(self.client, True, 100)
        await Outlet(self.client, DEVICES.outlet_tv).turn_on()

    async def on_long(self):
        await set_tvroom_lights(self.client, True, 30)

    async def off(self):
        await set_tvroom_lights(self.client, False)

    async def off_long(self):
        await set_tvroom_lights(self.client, False)
        await Outlet(self.client, DEVICES.outlet_tv).turn_off()

class SecondaryEntryMotionSensorHandler(hass_ae.entities.TFMotionSensorHandler):

    def __init__(self, client):
        self.client = client

    async def on(self):
        await Light(self.client, DEVICES.light_secondaryentry_roof).set_state(True, brightness=100)

    async def off(self):
        await Light(self.client, DEVICES.light_secondaryentry_roof).set_state(False)


async def set_livingroom_lights(client, on=True, brightess=None):
    await Light(client, DEVICES.light_livingroom_roof).set_state(on, brightness=brightess)
    await Light(client, DEVICES.light_livingroom_side).set_state(on, brightness=brightess)
    await Outlet(client, DEVICES.outlet_tablelamp_1).set_state(on)


async def set_tvroom_lights(client, on=True, brightess=None):
    await Outlet(client, DEVICES.outlet_whisky).set_state(on)


async def set_entry_lights(client, on=True, brightess=None):
    await Light(client, DEVICES.light_entry_roof_1).set_state(on, brightness=brightess)
    await Light(client, DEVICES.light_entry_roof_2).set_state(on, brightness=brightess)
    await Outlet(client, DEVICES.outlet_entrylight).set_state(on)


async def set_secondaryentry_lights(client, on=True, brightess=None):
    await Light(client, DEVICES.light_secondaryentry_roof).set_state(on, brightness=brightess)