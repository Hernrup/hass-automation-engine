import logging
from hass_ae.dl import Light

logger = logging.getLogger(__name__)

async def setup(client):
    await client.subscribe('state_changed', deconz_event_handler)
    await client.subscribe('deconz_event', deconz_event_handler)

async def deconz_event_handler(message, client):
    logger.info(f'I AM TRIGGERED')
    l1 = Light(client, 'light.i_dont_exist')
    await l1.turn_on()

        
    