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
        futures = {}

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
                    elif op == 'background':
                        future = self._executor.submit(args['fn'], *args['args'], **args['kwargs'])
                        futures[future] = coro
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

            if futures:
                completed, _ = wait(futures.keys(), timeout=timeout, return_when=FIRST_COMPLETED)
                for future in completed:
                    coro = futures.pop(future)
                    self._coros.append((coro, future.result()))
            else:
                if timeout:
                    time.sleep(timeout)

            now = time.time()
            for (wakeup, coro) in list(wakeups):
                if wakeup <= now:
                    wakeups.remove((wakeup, coro))
                    self._coros.append((coro, None))

scheduler = _Scheduler()
