"""A very simple co-routine scheduler.

Note: this is written to favour simple code over performance.
"""

class _Switch:
    def __await__(self):
        yield


# A future-like object that can be await-ed by co-routines and forces
# a co-routine switch.
switch = _Switch()


def schedule(coros):
    """Execute a list of co-routines until all have completed."""
    coros = list(coros)

    while len(coros):
        for coro in list(coros):
            try:
                coro.send(None)
            except StopIteration:
                coros.remove(coro)
