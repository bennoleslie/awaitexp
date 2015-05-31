"""A very simple co-routine scheduler that supports a sleep function

Interaction is through the `scheduler` singleton object.

Note: this is written to favour simple code over performance.
"""
from types import coroutine
import time
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from functools import wraps


@coroutine
def switch(**kwargs):
    return (yield kwargs)


async def sleep(delay):
    await switch(op='sleep', delay=delay)


def background(fn):
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        return await switch(op='background', fn=fn, args=args, kwargs=kwargs)
    return wrapper


class _Scheduler:
    def __init__(self):
        self._coros = []
        self._executor = ThreadPoolExecutor()

    def add_coro(self, coro):
        self._coros.append((coro, None))

    def run(self):
        """Execute a list of co-routines until all have completed."""
        # Copy argument list to avoid modification of arguments.
        wakeups = []
        futures = []

        while self._coros or wakeups or futures:
            # Copy the list for iteration, to enable removal from original
            # list.
            now = time.time()
            for (wakeup, coro) in list(wakeups):
                if wakeup <= now:
                    wakeups.remove((wakeup, coro))
                    self._coros.append((coro, None))

            for (future, coro) in list(futures):
                if future.done():
                    futures.remove((future, coro))
                    self._coros.append((coro, future.result()))

            if self._coros:
                for coro, value in list(self._coros):
                    try:
                        args = coro.send(value)
                        op = args.get('op')
                        if op == 'sleep':
                            wakeup = time.time() + args['delay']
                            self._coros.remove((coro, value))
                            wakeups.append((wakeup, coro))
                        elif op == 'background':
                            future = self._executor.submit(args['fn'], *args['args'], **args['kwargs'])
                            futures.append((future, coro))
                            self._coros.remove((coro, value))
                    except StopIteration:
                        self._coros.remove((coro, value))
            else:
                if wakeups:
                    next_wakeup = min(wakeup for (wakeup, _) in wakeups)
                    timeout = next_wakeup - now
                else:
                    timeout = None
                if futures:
                    wait([f for (f, _) in futures], timeout=timeout, return_when=FIRST_COMPLETED)
                else:
                    time.sleep(timeout)

scheduler = _Scheduler()
