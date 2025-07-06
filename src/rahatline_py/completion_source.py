import asyncio

class FutureCompletionSource:
    def __init__(self):
        self._future = asyncio.Future()
    
    @property
    def Promise(self):
        return self._future
    
    def Resolve(self, value):
        if not self._future.done():
            self._future.set_result(value)
    
    def Reject(self, reason):
        if not self._future.done():
            self._future.set_exception(Exception(reason))