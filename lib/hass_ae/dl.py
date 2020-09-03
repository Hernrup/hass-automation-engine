import enum

class Light():

    DOMAIN = 'light'

    def __init__(self, client, identity):
        self.identity = identity
        self.client = client
        self.full_identity = f'{self.DOMAIN}.{self.identity}'

    async def turn_on(self, brightness=None):
        await self.client.call_service(
            domain=self.DOMAIN,
            service='turn_on',
            data={"service_data": {"entity_id": self.full_identity}})

    async def turn_off(self):
        await self.client.call_service(
            domain=self.DOMAIN,
            service='turn_off',
            data={"service_data": {"entity_id": self.full_identity}})

    async def toggle(self):
        await self.client.call_service(
            domain=self.DOMAIN,
            service='toggle',
            data={"service_data": {"entity_id": self.full_identity}})


class TFSwitch():

    DOMAIN = 'switch'

    def __init__(self, client, identity):
        self.identity = identity
        self.client = client
        self.full_identity = f'{self.DOMAIN}.{self.identity}'

    async def check_event(self, data):
        print(data)
        if self.identity != data['event']['data']['id']:
            raise NotApplicableError(f'switch {self.identity} did not send this event')
        return TFSwitchState(data['event']['data']['event'])

class TFSwitchState(enum.Enum):
    on_long=1001
    on=1002
    on_release=1003
    off_long=2001
    off=2002
    off_release=2003

class Error(Exception):
    pass

class NotApplicableError(Error):
    pass