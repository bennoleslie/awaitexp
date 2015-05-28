"""A very simple co-routine scheduler.

Note: this is written to favour simple code over performance.
"""
from types import coroutine


@coroutine
def switch():
    yield


def run(coros):
    """Execute a list of co-routines until all have completed."""
    # Copy argument list to avoid modification of arguments.
    coros = list(coros)

    while len(coros):
        # Copy the list for iteration, to enable removal from original
        # list.
        for coro in list(coros):
            try:
                coro.send(None)
            except StopIteration:
                coros.remove(coro)
