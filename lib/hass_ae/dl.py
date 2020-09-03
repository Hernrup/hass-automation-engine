class Light():

    def __init__(self, client,identity):
        self.identity = identity
        self.client = client

    async def turn_on(self, brightness=None):
        await self.client.call_service(
            domain='light',
            service='turn_on',
            data={"service_data": {"entity_id": self.identity}})

    async def turn_off(self):
        await self.client.call_service(
            domain='light',
            service='turn_off',
            data={"service_data": {"entity_id": self.identity}})

    async def toggle(self):
        await self.client.call_service(
            domain='light',
            service='toggle',
            data={"service_data": {"entity_id": self.identity}})