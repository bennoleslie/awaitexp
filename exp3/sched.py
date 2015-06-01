"""A very simple co-routine scheduler that supports a sleep function

Interaction is through the `scheduler` singleton object.

Note: this is written to favour simple code over performance.
"""
from types import coroutine
import time


@coroutine
def switch(**kwargs):
    yield kwargs


async def sleep(delay):
    await switch(delay=delay)


class _Scheduler:
    def __init__(self):
        self._coros = []

    def add_coro(self, coro):
        self._coros.append(coro)

    def run(self):
        """Execute a list of co-routines until all have completed."""
        # Copy argument list to avoid modification of arguments.
        wakeups = []

        while self._coros:
            # Copy the list for iteration, to enable removal from original
            # list.
            for coro in list(self._coros):
                try:
                    args = coro.send(None)
                    if 'delay' in args:
                        wakeup = time.time() + args['delay']
                        self._coros.remove(coro)
                        wakeups.append((wakeup, coro))
                except StopIteration:
                    self._coros.remove(coro)

            if self._coros:
                timeout = 0
            else:
                if wakeups:
                    timeout = min(wakeup for (wakeup, _) in wakeups) - time.time()
                    if timeout < 0:
                        timeout = 0
                else:
                    timeout = None

            if timeout:
                time.sleep(timeout)

            now = time.time()
            for (wakeup, coro) in list(wakeups):
                if wakeup <= now:
                    wakeups.remove((wakeup, coro))
                    self._coros.append(coro)


scheduler = _Scheduler()
