#!/usr/bin/python3

import asyncio
import json
import websockets
import logging
import cachetools
import hass_ae.client as hac
import hass_ae.config
import hass_ae.automation
import hass_ae.entities


logger = logging.getLogger(__name__)

async def async_main(host, port, access_token):
    ws = hac.Websocket()
    state_manager = hass_ae.client.StateManager()
    client = hac.Client(ws)

    await client.connect(host, port)

    listen_task = asyncio.create_task(client.listen())

    await client.authenticate(access_token)

    states = await client.get_states()
    state_manager.load(states)
    
    await client.subscribe(
        'state_changed', 
        lambda data, client: state_changed_handler(data, client, state_manager)
        )

    await hass_ae.automation.setup(client, state_manager)

    await listen_task

async def state_changed_handler(data, client, state_manager):
    await state_manager.update(
        state=data['event']['data']['new_state']['entity_id'],
        value=data['event']['data']['new_state']['state']
        )

def configure_logging(log_level, ws_log_level):
    logging.basicConfig(
        format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
        level=log_level,
        datefmt="%H:%M:%S"
    )
    logging.getLogger('websockets.protocol').level = ws_log_level
    logging.getLogger('websockets.client').level = ws_log_level

def run():
    config = hass_ae.config.Config()

    level = logging.getLevelName(config['log_level'].upper())
    ws_level = logging.getLevelName(config['ws_log_level'].upper())
    configure_logging(level, ws_level) 

    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_main(
        host=config['host'],
        port=config['port'],
        access_token=config['access_token']
        ))
    loop.close()