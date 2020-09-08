import pprint
import enum

class InputSelect():

    DOMAIN = 'input_select'

    class States(enum.Enum):
        sleep = 1
        home = 2
        away = 3

    def __init__(self, identity, state_manager):
        self.identity = identity
        self.full_identity = f'{self.DOMAIN}.{self.identity}'
        self.state_manager = state_manager

    @property
    def state(self):
        raw = self.state_manager.get(self.full_identity)
        return self.States[raw.lower()]

