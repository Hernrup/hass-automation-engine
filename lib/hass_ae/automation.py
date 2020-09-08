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
    await client.subscribe('deconz_event', deconz_event_handler)
    await client.subscribe('state_changed', state_change_handler)

    ip = hass_ae.entities.InputSelect('i_home_state', state_manager)
    

async def deconz_event_handler(message, client):
    await NightSwitch(client).evaluate(message)
    await SecondaryEntrySwitch(client).evaluate(message)
    await LivingRoomSwitch(client).evaluate(message)
    await TvRoomSwitch(client).evaluate(message)
    
async def state_change_handler(message, client):
    await SecondaryEntryMotionSensor(client).evaluate(message)


class NightSwitch(TFSwitch):

    def __init__(self, client):
        super().__init__(client, DEVICES.switch_entry, self._handler)

    class _handler(TFSwitchHandler):
        @staticmethod
        async def on(client):
            await set_entry_lights(client, True)
            await set_livingroom_lights(client, True)
            await set_tvroom_lights(client, True)

        @staticmethod
        async def off(client):
            await set_entry_lights(client, False)
            await set_livingroom_lights(client, False)
            await set_tvroom_lights(client, False)
            await Outlet(client, DEVICES.outlet_tv).turn_off()

class SecondaryEntrySwitch(TFSwitch):

    def __init__(self, client):
        super().__init__(client, DEVICES.switch_entry, self._handler)

    class _handler(TFSwitchHandler):
        @staticmethod
        async def on(client):
            await set_entry_lights(client, True)
            await set_livingroom_lights(client, True)
            await set_tvroom_lights(client, True)

        @staticmethod
        async def off(client):
            await set_entry_lights(client, False)
            await set_livingroom_lights(client, False)
            await set_tvroom_lights(client, False)
            await Outlet(client, DEVICES.outlet_tv).turn_off()


class LivingRoomSwitch(TFSwitch):

    def __init__(self, client):
        super().__init__(client, DEVICES.switch_livingroom, self._handler)

    class _handler(TFSwitchHandler):
        @staticmethod
        async def on(client):
            await set_livingroom_lights(client, True, 100)
            await set_entry_lights(client, True, 100)

        @staticmethod
        async def on_long(client):
            await set_livingroom_lights(client, True, 30)
            await set_entry_lights(client, True, 30)

        @staticmethod
        async def off(client):
            await set_livingroom_lights(client, False)
            await set_entry_lights(client, False)

        @staticmethod
        async def off_long(client):
            await set_livingroom_lights(client, False)
            await set_entry_lights(client, False)

class TvRoomSwitch(TFSwitch):

    def __init__(self, client):
        super().__init__(client, DEVICES.switch_tvroom, self._handler)

    class _handler(TFSwitchHandler):
        @staticmethod
        async def on(client):
            await set_tvroom_lights(client, True, 100)
            await Outlet(client, DEVICES.outlet_tv).turn_on()

        @staticmethod
        async def on_long(client):
            await set_tvroom_lights(client, True, 30)

        @staticmethod
        async def off(client):
            await set_tvroom_lights(client, False)

        @staticmethod
        async def off_long(client):
            await set_tvroom_lights(client, False)
            await Outlet(client, DEVICES.outlet_tv).turn_off()


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


class SecondaryEntryMotionSensor(TFMotionSensor):

    def __init__(self, client):
        super().__init__(client, DEVICES.motionsensor_secondaryentry, self._handler)

    class _handler(TFMotionSensorHandler):
        @staticmethod
        async def on(client):
            await Light(client, DEVICES.light_secondaryentry_roof).set_state(True, brightness=100)

        @staticmethod
        async def off(client):
            await Light(client, DEVICES.light_secondaryentry_roof).set_state(False)