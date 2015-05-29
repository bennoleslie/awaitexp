# Await/async experiments

This is a small set of experiments / explorations into the await/async feature described in PEP-0492 (https://www.python.org/dev/peps/pep-0492/) and implemented in Python 3.5.


## Experiment 1 - Simplest scheduler.

The goal of experiment 1 is to have a essentially the simplest possible co-routine scheduler.
This is in juxtaposition to the relatively complex schedulers found in the standard asyncio module.

## Experiement 2 - Simple scheduler w/ sleep function

The goal of experiment 2 is to add an awaitable sleep co-routine function to our scheduler.
This adds a reasonable amount of complexity to the scheduler, although the sleep function itself is rather simple.
Whether or not this sleep aspect of the scheduler will be easily composable with other events in the future will be interesting.
