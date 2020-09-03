import dotenv
import os

class Config(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dotenv.load_dotenv(verbose=True)
        self._load()

    def _load(self):
        defaults = {
            'host':'localhost',
            'port':8123,
            'access_token': 'change-me',
            'log_level': 'info'
        }

        values = {k:os.getenv(k.upper(), defaults[k]) for k, v in defaults.items()}
        self.update(values)