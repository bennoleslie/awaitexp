"""A very simple co-routine scheduler that supports a sleep function

Interaction is through the `scheduler` singleton object.

Note: this is written to favour simple code over performance.
"""
from types import coroutine
import selectors
import time


@coroutine
def switch(**kwargs):
    return (yield kwargs)


async def sleep(delay):
    await switch(op='sleep', delay=delay)


async def io(fileobj, events):
    return await switch(op='io', fileobj=fileobj, events=events)


class _Scheduler:
    def __init__(self):
        self._coros = []
        self.selector = selectors.DefaultSelector()

    def add_coro(self, coro):
        self._coros.append((coro, None))

    def run(self):
        """Execute a list of co-routines until all have completed."""
        # Copy argument list to avoid modification of arguments.
        wakeups = []

        while self._coros:
            # Copy the list for iteration, to enable removal from original
            # list.
            for coro, value in list(self._coros):
                try:
                    args = coro.send(value)
                    op = args.get('op')
                    if op == 'sleep':
                        wakeup = time.time() + args['delay']
                        self._coros.remove((coro, value))
                        wakeups.append((wakeup, coro))
                    elif op == 'io':
                        self.selector.register(args['fileobj'], args['events'], coro)
                        self._coros.remove((coro, value))
                except StopIteration:
                    self._coros.remove((coro, value))

            if self._coros:
                timeout = 0
            else:
                if wakeups:
                    timeout = min(wakeup for (wakeup, _) in wakeups) - time.time()
                    if timeout < 0:
                        timeout = 0
                else:
                    timeout = None

            if len(self.selector.get_map()):
                for key, events in self.selector.select(timeout=timeout):
                    self.selector.unregister(key.fileobj)
                    self._coros.append((key.data, events))
            else:
                if timeout:
                    time.sleep(timeout)

            now = time.time()
            for (wakeup, coro) in list(wakeups):
                if wakeup <= now:
                    wakeups.remove((wakeup, coro))
                    self._coros.append((coro, None))


scheduler = _Scheduler()
