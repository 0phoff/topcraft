####################
# Python Profiling #
####################
import os
import logging

from ._memory import Memory, Memit, MemTrend
from ._time import Timer, Timeit, TimeTrend
from ._meta import AutoContextType, AutoDecoratorType, AutoIterType, combine_types

__all__ = ['Profiler', 'Profileit', 'ProfileTrend']
log = logging.getLogger(__name__)

# Get Profiling type
PROFILE_TYPE = os.environ.get('TOP_PROFILE', os.environ.get('PROFILE', '0'))
PROFILE_TYPE = '1' if PROFILE_TYPE.lower() in {'t', 'time', 'timer', 'timeit'} else PROFILE_TYPE
PROFILE_TYPE = '2' if PROFILE_TYPE.lower() in {'m', 'mem', 'memory', 'memit'} else PROFILE_TYPE
try:
    PROFILE_TYPE = int(PROFILE_TYPE)
except ValueError:
    log.error('Unkown profile type: "%s", disabling profiler (please choose "time" or "memory").', PROFILE_TYPE)
    PROFILE_TYPE = 0


class Profiler(metaclass=combine_types(AutoContextType, AutoDecoratorType)):
    """
    Uses `top.Timer` or `top.Memory` depending on the value of the `TOP_PROFILE` (or `PROFILE`) environment variable.
    If the environment variable is set to "time", we use the `Timer` class.
    If it is set to "mem" or "memory", we use the `Memory` class.
    In all other cases, this class acts as a Dummy that does nothing.
    For information on its arguments, please check the `top.Timer` and `top.Memory` classes.

    This class is very handy if you need to measure both Time and Memory consumption of a piece of code.
    Simply use this `Profiler` class instead of `Memory` and `Timer`:

    >>> # Use this class as a decorator
    >>> @top.Profiler
    ... def myfunc():
    ...     pass

    >>> # Passing in arguments specifically for Mem is allowed
    >>> with top.Profiler(poll_interval=1e-6):
    ...     pass

    You can now run your script and set the TOP_PROFILE environment variable.

    >>> # Running script normally has no overhead for decorators and barely any overhead for contextmanagers
    >>> ./script.py

    >>> # Running time profiling
    >>> TOP_PROFILE=time ./script.py

    >>> # Running memory profiling
    >>> TOP_PROFILE=mem ./script.py
    """
    def __new__(cls, unit='X', label='profile', verbose=True, store=None, *, poll_interval=0):
        if PROFILE_TYPE == 1:
            return Timer(unit, label, verbose, store)
        if PROFILE_TYPE == 2:
            return Memory(unit, label, verbose, store, poll_interval=poll_interval)
        return super().__new__(cls)

    def reset(self):
        pass

    def start(self):
        pass

    def split(self):
        return 0

    def stop(self):
        return 0

    def __enter__(self):
        return None

    def __exit__(self, ex_type, ex_value, trace):
        return False

    def __call__(self, fn):
        return fn


class Profileit(metaclass=AutoIterType):
    """
    Uses `top.Timeit` or `top.Memit` depending on the value of the `TOP_PROFILE` (or `PROFILE`) environment variable.
    If the environment variable is set to "time", we use the `Timeit` class.
    If it is set to "mem" or "memory", we use the `Memit` class.
    In all other cases, this class acts as a Dummy that does nothing.
    For information on its arguments, please check the `top.Timeit` and `top.Memit` classes.

    This class is very handy if you need to benchmark both Time and Memory consumption of a piece of code.
    Simply use this `Profileit` class instead of `Memit` and `Timeit`:

    >>> # Use this profileit iterator as you would use Memit/Timeit
    >>> # All arguments or allowed, the class only forwards the necessary ones.
    >>> for p in Profileit(poll_interval=1e-6):
    ...     pass

    You can now run your script and set the TOP_PROFILE environment variable.

    >>> # Running script normally will simply run the code inside the iterator once and yield a dummy `Profiler` object.
    >>> ./script.py

    >>> # Running time profiling
    >>> TOP_PROFILE=time ./script.py

    >>> # Running memory profiling
    >>> TOP_PROFILE=mem ./script.py
    """
    def __new__(cls, repeat=1, unit='X', label='profile', verbose=False, store=None, *, poll_interval=0):
        if PROFILE_TYPE == 1:
            return Timeit(repeat, unit, label, verbose, store)
        if PROFILE_TYPE == 2:
            return Memit(repeat, unit, label, verbose, store, poll_interval=poll_interval)
        return super().__new__(cls)

    def reset(self):
        pass

    def __iter__(self):
        yield Profiler()


class ProfileTrend(metaclass=AutoIterType):
    """
    Uses `top.TimeTrend` or `top.MemTrend` depending on the value of the `TOP_PROFILE` (or `PROFILE`) environment variable.
    If the environment variable is set to "time", we use the `TimeTrend` class.
    If it is set to "mem" or "memory", we use the `MemTrend` class.
    In all other cases, this class acts as a Dummy that does nothing.
    For information on its arguments, please check the `top.TimeTrend` and `top.MemTrend` classes.

    This class is very handy if you need to benchmark both Time and Memory consumption of a piece of code.
    Simply use this `Profileit` class instead of `MemTrend` and `TimeTrend`:

    >>> # Use this profileit iterator as you would use MemTrend/TimeTrend
    >>> # All arguments or allowed, the class only forwards the necessary ones.
    >>> for i, p in ProfileTrend(range(10,101,10), poll_interval=1e-6):
    ...     pass

    You can now run your script and set the TOP_PROFILE environment variable.

    >>> # Running script normally will simply run the code inside the iterator once and yield a dummy `Profiler` object.
    >>> ./script.py

    >>> # Running time profiling
    >>> TOP_PROFILE=time ./script.py

    >>> # Running memory profiling
    >>> TOP_PROFILE=mem ./script.py
    """
    def __new__(cls, trend_range=10, repeat=1, unit='X', label='profile', verbose=True, *, poll_interval=0):
        if PROFILE_TYPE == 1:
            return TimeTrend(trend_range, repeat, unit, label, verbose)
        if PROFILE_TYPE == 2:
            return MemTrend(trend_range, repeat, unit, label, verbose, poll_interval=poll_interval)
        return super().__new__(cls)

    def __init__(self, trend_range=10, *args, **kwargs):
        self.trend_range = trend_range if isinstance(trend_range, range) else range(trend_range)

    def reset(self):
        pass

    def __iter__(self):
        yield (self.trend_range.start, Profiler())
