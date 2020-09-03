import logging
from hass_ae.dl import Light, TFSwitch, TFSwitchState
import hass_ae.dl
import enum
import time

logger = logging.getLogger(__name__)

DEVICES = dict(
    test_light='l_tf_4',
    test_switch='sw_tf_4'
)

async def setup(client):
    await client.subscribe('deconz_event', deconz_event_handler)
    await Light(client, DEVICES['test_light']).turn_off()

async def deconz_event_handler(message, client):
    logger.info(f'I AM TRIGGERED')
    print(message)

    try:
        signal = await TFSwitch(client, DEVICES['test_switch']).check_event(message)
        print(signal)
    except hass_ae.dl.NotApplicableError as e:
        logger.info(str(e))


    await Light(client, DEVICES['test_light']).toggle()
    