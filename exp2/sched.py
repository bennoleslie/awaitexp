"""A very simple co-routine scheduler that supports a sleep function

Note: this is written to favour simple code over performance.
"""
from types import coroutine
import time

@coroutine
def switch(**kwargs):
    yield kwargs


async def sleep(delay):
    await switch(delay=delay)


def run(coros):
    """Execute a list of co-routines until all have completed."""
    # Copy argument list to avoid modification of arguments.
    coros = list(coros)
    wakeups = []

    while coros or wakeups:
        # Copy the list for iteration, to enable removal from original
        # list.
        now = time.time()
        for (wakeup, coro) in list(wakeups):
            if wakeup <= now:
                wakeups.remove((wakeup, coro))
                coros.append(coro)

        if coros:
            for coro in list(coros):
                try:
                    args = coro.send(None)
                    if 'delay' in args:
                        wakeup = time.time() + args['delay']
                        coros.remove(coro)
                        wakeups.append((wakeup, coro))
                except StopIteration:
                    coros.remove(coro)
        else:
            next_wakeup = min(wakeup for (wakeup, _) in wakeups)
            time.sleep(next_wakeup - now)
