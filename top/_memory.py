#################################
# Code Memory Usage Measurement #
#################################
import gc
import logging
import os
import statistics
from collections import defaultdict
from functools import wraps
from memory_profiler import Pipe, Process, choose_backend, _get_memory

from ._meta import AutoContextType, AutoDecoratorType, AutoIterType, combine_types

__all__ = ['Mem', 'Memit', 'MemTrend']
log = logging.getLogger(__name__)


class MemTimer(Process):
    START = 0
    SPLIT = 1
    STOP = 2

    def __init__(self, monitor_pid, interval, pipe, *args, include_children=False, **kw):
        super().__init__(*args, **kw)
        self.monitor_pid = monitor_pid
        self.interval = interval
        self.pipe = pipe
        self.include_children = include_children
        try:
            self.backend = choose_backend('psutil_uss')
        except KeyError:
            self.backend = choose_backend()

    def run(self):
        start_mem = _get_memory(
            self.monitor_pid,
            self.backend,
            include_children=self.include_children,
        )
        max_mem = 0

        stop, split = False, False
        self.pipe.send(self.START)
        while True:
            mem = _get_memory(
                self.monitor_pid,
                self.backend,
                include_children=self.include_children,
            )
            max_mem = max(max_mem, mem)

            if stop:
                break
            elif split:
                split = False
                self.pipe.send(max(0, max_mem - start_mem))
                start_mem = _get_memory(
                    self.monitor_pid,
                    self.backend,
                    include_children=self.include_children,
                )
                max_mem = 0

            if (self.pipe.poll(self.interval)):
                value = self.pipe.recv()
                if value == self.STOP:
                    stop = True
                elif value == self.SPLIT:
                    split = True

        self.pipe.send(max(0, max_mem - start_mem))
        self.pipe.close()


class Mem(metaclass=combine_types(AutoContextType, AutoDecoratorType)):
    """
    This class allows you to measure code memory usage.
    You can use it in various different ways:
        - start() - split() - stop() methods
        - contextmanager
        - function decorator

    Args:
        unit (b, kb, mb, gb):
            Memory unit; Default 'Mb'
        label (str):
            Default label to use when stopping the profiler
        verbose (boolean):
            Whether to log times
        store (dict-like):
            Object to store timings instead of logging (should likely not be used by user)
        poll_interval (number):
            Seconds the monitoring process waits for input between memory measurements

    Note:
        When benchmarking a piece of code, it is usually a good idea to run it once first,
        as it will initialize "global" memory.
        The `Memit` class takes care of this automatically.
    """
    _units = {
        'b':  2 ** 20,
        'kb': 2 ** 10,
        'mb': 2 ** 0,
        'gb': 2 ** -10,
    }

    def __init__(self, unit='Mb', label='memory', verbose=True, store=None, *, poll_interval=0):
        self.label = label
        self.verbose = verbose
        self.poll_interval = poll_interval
        self.unit = unit if unit.lower() in self._units else 'Mb'
        self.unit_factor = self._units[self.unit.lower()]
        if isinstance(store, dict):
            self.store = store
            self.stop = self._stop_store
            self.split = self._split_store

        self._memtimer = None
        self._pipe = None
        self.reset()

    def reset(self):
        self.value = None
        self._splits = 0
        if self._memtimer is not None:
            self._pipe.send(MemTimer.STOP)
            self._pipe.recv()
            self._memtimer.join()
            self._memtimer = None
            self._pipe = None

    def start(self):
        self.reset()
        pipe, self._pipe = Pipe()
        self._memtimer = MemTimer(os.getpid(), self.poll_interval, pipe, include_children=True)
        self._memtimer.start()
        self._pipe.recv()

    def split(self):
        gc.collect()
        self._pipe.send(MemTimer.SPLIT)
        self._splits += 1
        value = self._pipe.recv() * self.unit_factor

        if self.verbose:
            log.info('%s %d: %.3f%s', self.label, self._splits, value, self.unit)

        return value

    def stop(self):
        gc.collect()
        self._pipe.send(MemTimer.STOP)
        self.value = self._pipe.recv() * self.unit_factor

        if self.verbose:
            label = self.label if self._splits == 0 else f'{self.label} {self._splits+1}'
            log.info('%s: %.3f%s', label, self.value, self.unit)

        self._memtimer.join()
        self._memtimer = None
        self._pipe = None
        return self.value

    def _split_store(self):
        gc.collect()
        self._pipe.send(MemTimer.SPLIT)
        self._splits += 1
        value = self._pipe.recv() * self.unit_factor

        self.store[f'{self.label} {self._splits}'] = value
        if self.verbose:
            log.info('%s %d: %.3f%s', self.label, self._splits, value, self.unit)

    def _stop_store(self):
        gc.collect()
        self._pipe.send(MemTimer.STOP)
        self.value = self._pipe.recv() * self.unit_factor

        label = self.label if self._splits == 0 else f'{self.label} {self._splits+1}'
        self.store[label] = self.value
        if self.verbose:
            log.info('%s: %.3f%s', label, self.value, self.unit)

        self._memtimer.join()
        self._memtimer = None
        self._pipe = None

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

    def __del__(self):
        self.reset()


class Memit(metaclass=AutoIterType):
    """
    This class allows you to benchmark the memory of a certain piece of code, by runnning it multiple times.
    It will automatically run your code once before starting the benchmark.

    Args:
        repeat (int):
            Number of times to run the code
        unit (b, kb, mb, gb):
            Memory unit
        label (str):
            Default label to use when stopping the profiler
        verbose (boolean):
            Whether to log intermediate loop times
        store (dict-like):
            Object to store timings instead of logging (should likely not be used by user)
        poll_interval (number):
            Seconds the monitoring process waits for input between memory measurements

    Note:
        In order to get consistent results, we manually run the garbage collector after every loop.
        We do not disable the automatic garbage collector, as a real python run would have it enabled,
        thus allowing to remove potentially unused memory.

    Example:
        >>> for _ in Memit(10):
        ...     # benchmark code
        ...     pass

        >>> for m in Memit(100):
        ...     # setup code
        ...     m.start()
        ...     # first part
        ...     m.split()
        ...     # second part
        ...     m.stop()

        >>> for m in Memit(1000):
        ...     # setup code
        ...     with m:
        ...         # benchmark code
        ...         pass
    """
    def __init__(self, repeat=1, unit='Mb', label='memory', verbose=False, store=None, *, poll_interval=0):
        self.repeat = repeat
        self.label = label
        self.unit = unit if unit.lower() in Mem._units else 'Mb'
        self.verbose = verbose
        self.poll_interval = poll_interval
        self.values = defaultdict(list)

        if store is not None:
            self.store = store
            self.process_results = self._store_results
        else:
            self.process_results = self._print_results

    def reset(self):
        self.values = defaultdict(list)

    def __iter__(self):
        if len(self.values):
            log.warning('self.values is not empty, consider calling reset between benchmarks')

        bg = Mem(self.unit, self.label, False, {}, poll_interval=self.poll_interval)
        fg = Mem(self.unit, self.label, False, {}, poll_interval=self.poll_interval)

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
                    f'{name:<{maxlen}} worst {max(val):.3f}{self.unit} '
                    f'[mean {statistics.fmean(val):.3f} ± {statistics.stdev(val):.3f}{self.unit}]',
                )
            else:
                log.info(f'{name:<{maxlen}} worst {max(val):.3f}{self.unit}')

    def _store_results(self, values):
        if self.verbose:
            self._print_results(values)

        for name, val in values.items():
            self.store[name] = max(val)


class MemTrend(metaclass=AutoIterType):
    """
    This class allows you to benchmark memory trends of a certain piece of code,
    by runnning it multiple times with an increasing variable.
    It works by yielding from a `Memit` class multiple times, with a different increasing number each time.

    Args:
        trend_range (int or range):
            The increasing number that is returned each loop
        repeat (int):
            Number of times we run each trend to get statistics
        unit (b, kb, mb, gb):
            Memory unit
        label (str):
            Default label to use for the profiler
        verbose (boolean):
            Whether to log intermediate loop tim
        store (dict-like):
            Object to store timings instead of logging (should likely not be used by user)
        poll_interval (number):
            Seconds the monitoring process waits for input between memory measurements

    Note:
        In order to get consistent results, we manually run the garbage collector after every loop.
        We do not disable the automatic garbage collector, as a real python run would have it enabled,
        thus allowing to remove potentially unused memory.

    Example:
        >>> # Run some code using the `i` variable, which will range from [10,101) with a stepsize of 10
        >>> # Note that the `m` variable is the same as returned by `Memit`
        >>> for i, m in MemTrend(range(10,101,10)):
        >>>     pass
    """
    def __init__(self, trend_range=10, repeat=1, unit='Mb', label='memory', verbose=True, *, poll_interval=0):
        self.trend_range = trend_range if isinstance(trend_range, range) else range(trend_range)
        self.repeat = repeat
        self.label = label
        self.unit = unit if unit.lower() in Mem._units else 'Mb'
        self.verbose = verbose
        self.poll_interval = poll_interval
        self.values = defaultdict(list)

    def reset(self):
        self.values = defaultdict(list)

    def __iter__(self):
        self.reset()
        memit = Memit(self.repeat, self.unit, self.label, False, self.poll_interval, {})
        trend_len = len(str(self.trend_range.stop))

        for trend in self.trend_range:
            for m in memit:
                yield trend, m

            for name, value in memit.store.items():
                self.values[name].append(value)

            if self.verbose:
                trend_mems = ', '.join(f'{n}: {v:.3f}{self.unit}' for n, v in memit.store.items())
                log.info(f'Trend {trend:>{trend_len}}: {trend_mems}')

            memit.reset()
