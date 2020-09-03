
#!/usr/bin/python4

import asyncio
import json
import websockets
import logging
import cachetools

import service.client as hac

HOST = 'hass.hernrup.se'
PORT = '8123'
ACCESS_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJlM2JjZTkyNDU0OWI0ODVlYjM0MmQ2NDRhMjUzZmFkYSIsImlhdCI6MTU5ODk5Njg5MiwiZXhwIjoxOTE0MzU2ODkyfQ.UDwPGAkA0spvpyGsMAuiKx9hfCU8EZohFOQtFM2PhJY'

logger = logging.getLogger(__name__)

async def main_loop(client):
    await client.connect(HOST, PORT)
    await client.authenticate(ACCESS_TOKEN)
    await client.subscribe('state_changed', deconz_event_handler)
    await client.subscribe('deconz_event', deconz_event_handler)
    await client.listen()

async def deconz_event_handler(message, client):
    logger.info(f'I GOT MY MESSAGE')
    await client.call_service(
        domain='light',
        service='turn_on',
        data={"service_data": {"entity_id": "light.i_dont_exist"}})

def main():
    logging.basicConfig(
        format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
        level=logging.DEBUG,
        datefmt="%H:%M:%S"
    )

    ws = hac.Websocket()
    client = hac.Client(ws)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_loop(client))
    loop.close()

if __name__ == '__main__':
    main()
