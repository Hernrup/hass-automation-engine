import abc 

class BooleanStateChangedHandler(abc.ABC):

    def on(self):
        pass

    def off(self):
        pass


class TFSwitchHandler(abc.ABC):

    async def on(self):
        pass

    async def on_long(self):
        pass

    async def on_release(self):
        pass

    async def off(self):
        pass

    async def off_long(self):
        pass

    async def off_release(self):
        pass


class TFMotionSensorHandler(abc.ABC):

    async def on(self):
        pass

    async def off(self):
        pass


