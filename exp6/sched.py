"""A very simple co-routine scheduler that supports a sleep function

Interaction is through the `scheduler` singleton object.

Note: this is written to favour simple code over performance.
"""
from types import coroutine
import selectors
import time
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from functools import wraps
import socket

BUFSIZE = 4096

@coroutine
def switch(**kwargs):
    return (yield kwargs)


async def sleep(delay):
    await switch(op='sleep', delay=delay)


async def io(fileobj, events):
    return await switch(op='io', fileobj=fileobj, events=events)


def background(fn):
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        return await switch(op='background', fn=fn, args=args, kwargs=kwargs)
    return wrapper


class _Scheduler:
    def __init__(self):
        self._coros = []
        self.selector = selectors.DefaultSelector()
        self._executor = ThreadPoolExecutor()
        self._rsock, self._wsock = socket.socketpair()
        self._rsock.setblocking(False)
        self.selector.register(self._rsock, selectors.EVENT_READ)

    def add_coro(self, coro):
        self._coros.append((coro, None))

    def _drain_self(self):
        while True:
            try:
                data = self._rsock.recv(BUFSIZE)
                if not data:
                    break
            except BlockingIOError:
                break

    def _background_done(self, fut):
        self._wsock.send(b'\0')

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
                    elif op == 'io':
                        self.selector.register(args['fileobj'], args['events'], coro)
                        self._coros.remove((coro, value))
                    elif op == 'background':
                        future = self._executor.submit(args['fn'], *args['args'], **args['kwargs'])
                        future.add_done_callback(self._background_done)
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

            if len(self.selector.get_map()) > 1 or futures:
                for key, events in self.selector.select(timeout=timeout):
                    if key.fileobj is self._rsock:
                        self._drain_self()
                        completed, _ = wait(futures.keys(), timeout=0, return_when=FIRST_COMPLETED)
                        for future in completed:
                            coro = futures.pop(future)
                            self._coros.append((coro, future.result()))
                    else:
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
