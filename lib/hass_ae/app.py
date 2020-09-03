#!/usr/bin/python3

import asyncio
import json
import websockets
import logging
import cachetools
import hass_ae.client as hac
import hass_ae.config
import hass_ae.automation


logger = logging.getLogger(__name__)

async def main_loop(client, host, port, access_token):
    await client.connect(host, port)
    await client.authenticate(access_token)
    await client.listen(blocking=False)
    await hass_ae.automation.setup(client)
    await client.listen(blocking=True)

def run():
    config = hass_ae.config.Config()

    level = logging.getLevelName(config['log_level'].upper())
    logging.basicConfig(
        format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
        level=level,
        datefmt="%H:%M:%S"
    )

    ws = hac.Websocket()
    client = hac.Client(ws)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_loop(
        client=client,
        host=config['host'],
        port=config['port'],
        access_token=config['access_token']
        ))
    loop.close()