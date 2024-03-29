###################################
# Code Time Execution Measurement #
###################################
import gc
import logging
import statistics
from collections import defaultdict
from functools import wraps

from ._meta import AutoContextType, AutoDecoratorType, AutoIterType, combine_types
from ._gc import ToggleGC

__all__ = ['Time', 'Timeit', 'TimeTrend']
log = logging.getLogger(__name__)

# Use perf_counter_ns if available
try:
    from time import perf_counter_ns as perf_counter
    time_factor = 1e0
except ImportError:
    from time import perf_counter
    time_factor = 1e9


class Time(metaclass=combine_types(AutoContextType, AutoDecoratorType)):
    """
    This class allows you to measure code execution time.
    You can use it in various different ways:
        - start() - split() - stop() methods
        - contextmanager
        - function decorator

    Args:
        unit (s, ms, us or ns):
            Time unit
        label (str):
            Label to use for logging the timer
        verbose (boolean):
            Whether to log times
        store (dict-like):
            Object to store timings instead of logging (should likely not be used by user)

    Note:
        When benchmarking a piece of code, it is usually a good idea to run it once first,
        as it will initialize "global" variables, which takes time.
        The `Timeit` class takes care of this automatically.
    """
    _units = {
        's': 1e-9 * time_factor,
        'ms': 1e-6 * time_factor,
        'us': 1e-3 * time_factor,
        'ns': 1e0 * time_factor,
    }

    def __init__(self, unit='s', label='time', verbose=True, store=None):
        self.label = label
        self.verbose = verbose
        self.unit = unit if unit.lower() in self._units else 's'
        self.unit_factor = self._units[self.unit.lower()]
        if isinstance(store, dict):
            self.store = store
            self.stop = self._stop_store
            self.split = self._split_store

        self.reset()

    def reset(self):
        self.value = None
        self._start = None
        self._splits = 0

    def start(self):
        self.value = None
        self._start = perf_counter()

    def split(self):
        value = (perf_counter() - self._start) * self.unit_factor
        self._splits += 1
        if self.verbose:
            log.info('%s %d: %.3f%s', self.label, self._splits, value, self.unit)

        self._start = perf_counter()
        return value

    def stop(self):
        self.value = (perf_counter() - self._start) * self.unit_factor
        if self.verbose:
            label = self.label if self._splits == 0 else f'{self.label} {self._splits+1}'
            log.info('%s: %.3f%s', label, self.value, self.unit)

        self._start = None
        return self.value

    def _split_store(self):
        value = (perf_counter() - self._start) * self.unit_factor
        self._splits += 1
        self.store[f'{self.label} {self._splits}'] = value
        if self.verbose:
            log.info('%s %d: %.3f%s', self.label, self._splits, value, self.unit)
        self._start = perf_counter()

    def _stop_store(self):
        self.value = (perf_counter() - self._start) * self.unit_factor
        label = self.label if self._splits == 0 else f'{self.label} {self._splits+1}'
        self.store[label] = self.value
        if self.verbose:
            log.info('%s: %.3f%s', label, self.value, self.unit)
        self._start = None

    def __enter__(self):
        self.start()

    def __exit__(self, ex_type, ex_value, trace):
        self.stop()
        return False

    def __call__(self, fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            verbose = self.verbose
            label = self.label

            self.verbose = True
            self.label = fn.__name__
            with self:
                retval = fn(*args, **kwargs)

            self.verbose = verbose
            self.label = label

            return retval

        return inner


class Timeit(metaclass=AutoIterType):
    """
    This class allows you to benchmark the time of a certain piece of code, by runnning it multiple times.
    It will automatically run your code once before starting the benchmark.

    Args:
        repeat (int):
            Number of times to run the code
        unit (s, ms, us or ns):
            Time unit
        label (str):
            Default label to use for the timer
        verbose (boolean):
            Whether to log intermediate loop values
        store (dict-like):
            Object to store timings instead of logging (should likely not be used by user)

    Note:
        We disable the automatic garbage collector when running the benchmark in order to have consistent results.
        Between loops, we then manually run it.

    Example:
        >>> for _ in Timeit(10):
        ...     # benchmark code
        ...     pass

        >>> for t in Timeit(100):
        ...     # setup code
        ...     t.start()
        ...     # first part of code
        ...     t.split()
        ...     # second part
        ...     t.stop()

        >>> for t in Timeit(1000):
        ...     # setup code
        ...     with t:
        ...         # benchmark code
        ...         pass
    """
    def __init__(self, repeat=1, unit='s', label='time', verbose=False, store=None):
        self.repeat = repeat
        self.label = label
        self.unit = unit if unit.lower() in Time._units else 's'
        self.verbose = verbose
        self.values = defaultdict(list)

        if isinstance(store, dict):
            self.store = store
            self.process_results = self._store_results
        else:
            self.process_results = self._print_results

    def reset(self):
        self.values = defaultdict(list)

    def __iter__(self):
        if len(self.values):
            log.warning('self.values is not empty, consider calling reset between benchmarks')

        bg = Time(self.unit, self.label, False, {})
        fg = Time(self.unit, self.label, False, {})

        with ToggleGC(False):
            for i in range(self.repeat+1):
                with bg:
                    yield fg

                if i == 0:
                    fg.reset()
                    fg.store = {}
                    gc.collect()
                    continue

                if fg.store:
                    for name, value in fg.store.items():
                        self.values[name].append(value)
                else:
                    self.values[self.label].append(bg.store[self.label])

                if self.verbose:
                    log.info('Loop %d: %.3f%s', i, bg.store[self.label], self.unit)

                fg.reset()
                fg.store = {}
                gc.collect()

        self.process_results(self.values)

    def _print_results(self, values):
        maxlen = max(len(k) for k in values.keys()) + 1
        for name, val in values.items():
            name = name + ':'
            if self.repeat > 1:
                log.info(
                    f'{name:<{maxlen}} best {min(val):.3f}{self.unit} '
                    f'[mean {statistics.fmean(val):.3f} ± {statistics.stdev(val):.3f}{self.unit}]',
                )
            else:
                log.info(f'{name:<{maxlen}} best {min(val):.3f}{self.unit}')

    def _store_results(self, values):
        if self.verbose:
            self._print_results(values)

        for name, val in values.items():
            self.store[name] = min(val)


class TimeTrend(metaclass=AutoIterType):
    """
    This class allows you to benchmark time trends of a certain piece of code,
    by runnning it multiple times with an increasing variable.
    It works by yielding from a `Timeit` class multiple times, with a different increasing number each time.

    Args:
        trend_range (int or range):
            The increasing number that is returned each loop
        repeat (int):
            Number of times we run each trend to get statistics
        unit (s, ms, us or ns):
            Time unit
        label (str):
            Default label to use for the profiler
        verbose (boolean):
            Whether to log intermediate loop values
        store (dict-like):
            Object to store timings instead of logging (should likely not be used by user)

    Note:
        We disable the automatic garbage collector when running the benchmark in order to have consistent results.
        Between loops, we then manually run it.

    Example:
        >>> # Run some code using the `i` variable, which will range from [10,101) with a stepsize of 10
        >>> # Note that the `t` variable is the same as returned by `Timeit`
        >>> for i, t in MemTrend(range(10,101,10)):
        >>>     pass
    """
    def __init__(self, trend_range=10, repeat=1, unit='s', label='time', verbose=True):
        self.trend_range = trend_range if isinstance(trend_range, range) else range(trend_range)
        self.repeat = repeat
        self.label = label
        self.unit = unit if unit.lower() in Time._units else 's'
        self.verbose = verbose
        self.values = defaultdict(list)

    def reset(self):
        self.values = defaultdict(list)

    def __iter__(self):
        self.reset()
        timeit = Timeit(self.repeat, self.unit, self.label, False, {})
        trend_len = len(str(self.trend_range.stop))

        for trend in self.trend_range:
            for t in timeit:
                yield (trend, t)

            for name, value in timeit.store.items():
                self.values[name].append(value)

            if self.verbose:
                trend_times = ', '.join(f'{n}: {v:.3f}{self.unit}' for n, v in timeit.store.items())
                log.info(f'Trend {trend:>{trend_len}}: {trend_times}')

            timeit.reset()
