import asyncio

async def m():
    task = asyncio.create_task(a())
    task.cancel()
    await asyncio.sleep(5)

async def a():
    await asyncio.sleep(2)
    print('yeeee')

loop = asyncio.get_event_loop()
loop.run_until_complete(m())
loop.close()