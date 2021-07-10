import logging
import asyncio
import hass_ae
import hass_ae.client
import hass_ae.config
import hass_ae.components


def run(config, async_fn):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_main(
        host=config['host'],
        port=config['port'],
        access_token=config['access_token'],
        async_fn=async_fn
        ))
    loop.close()


async def async_main(host, port, access_token, async_fn):
    ws = hass_ae.client.Websocket()
    state_manager = hass_ae.client.StateManager()
    registry = hass_ae.components.ComponentRegistry()
    client = hass_ae.client.Client(ws)

    await client.connect(host, port)

    listen_task = asyncio.create_task(client.listen())

    await client.authenticate(access_token)

    states = await client.get_states()
    state_manager.load(states)
    
    await client.subscribe(
        'state_changed', 
        lambda data, client: state_manager.event_callback(data)
        )

    await async_fn(
        client=client,
        state_manager=state_manager,
        registry=registry
        )

    await listen_task