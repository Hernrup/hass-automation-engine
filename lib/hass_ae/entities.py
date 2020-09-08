import pprint

class StateManager():

    def __init__(self, client):
        self.client = client
        self._states = {}

    @property
    def states(self):
        return self._states
   
    def get(self, state, default=None):
        return self.get(state, default)

    def update(self, state, value):
        self._states[state] = value

    async def refresh(self):
        data = await self.client.get_states()
        self._states = self._parse_from_raw_states(data)

    @classmethod
    def _parse_from_raw_states(cls, data):
        return {d['entity_id']: d['state'] for d in data}
