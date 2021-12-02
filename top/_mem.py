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

from ._util import AutoDecoratorContextManagerType

__all__ = ['Profiler', 'Profileit']
log = logging.getLogger('startup.profile')


class MemTimer(Process):
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
        self.pipe.send(0)
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
                self.pipe.send(max(0, max_mem - start_mem))
                start_mem = _get_memory(
                    self.monitor_pid,
                    self.backend,
                    include_children=self.include_children,
                )
                max_mem = 0

            if (self.pipe.poll(self.interval)):
                value = self.pipe.recv()
                if value == 1:
                    split = True
                else:
                    stop = True

        self.pipe.send(max(0, max_mem - start_mem))
        self.pipe.close()


class Profiler(metaclass=AutoDecoratorContextManagerType):
    """
    This class allows you to measure code memory usage.
    You can use it in various different ways:
        - start() - split() - stop() methods
        - contextmanager
        - function decorator

    Args:
        unit (b, kb, mb, gb): Memory unit; Default 'Mb'
        label (str): Default label to use when stopping the profiler; Default 'memory'
        verbose (boolean): Whether to log times; Default True
        poll_interval (number): Seconds the monitoring process waits for input between memory measurements; Default 1ms
        store (dict-like): Object to store timings instead of logging (should likely not be used by user); Default None

    Note:
        When benchmarking a piece of code, it is usually a good idea to run it once first,
        as it will initialize "global" memory.
        The `Profileit` class takes care of this automatically.
    """
    _units = {
        'b':  2 ** 20,
        'kb': 2 ** 10,
        'mb': 2 ** 0,
        'gb': 2 ** -10,
    }

    def __init__(self, unit='Mb', label='memory', verbose=True, poll_interval=1e-3, store=None):
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
            self._pipe.send(0)
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
        self._pipe.send(1)
        self._splits += 1
        value = self._pipe.recv() * self.unit_factor

        if self.verbose:
            log.info('%s %d: %.3f%s', self.label, self._splits, value, self.unit)

        return value

    def stop(self):
        self._pipe.send(0)
        self.value = self._pipe.recv() * self.unit_factor

        if self.verbose:
            label = self.label if self._splits == 0 else f'{self.label} {self._splits+1}'
            log.info('%s: %.3f%s', label, self.value, self.unit)

        self._memtimer.join()
        self._memtimer = None
        self._pipe = None
        return self.value

    def _split_store(self, label):
        self._pipe.send(1)
        self._splits += 1
        value = self._pipe.recv() * self.unit_factor
        self.store[f'{self.label} {self._splits}'] = value

    def _stop_store(self):
        self._pipe.send(0)
        self.value = self._pipe.recv() * self.unit_factor

        label = self.label if self._splits == 0 else f'{self.label} {self._splits+1}'
        self.store[label] = self.value

        self._memtimer.join()
        self._memtimer = None
        self._pipe = None

    def __enter__(self):
        self.start()

    def __exit__(self, ex_type, ex_value, trace):
        self.stop()

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


class Profileit:
    """
    This class allows you to benchmark the memory of a certain piece of code, by runnning it multiple times.
    It will automatically run your code once before starting the benchmark.

    Args:
        repeat (int): Number of times to run the code
        unit (b, kb, mb, gb): Memory unit; Default 'Mb'
        label (str): Default label to use when stopping the profiler; Default 'total'
        verbose (boolean): Whether to log intermediate loop times; Default True
        poll_interval (number): Seconds the monitoring process waits for input between memory measurements; Default 1ms

    Note:
        In order to get consistent results, we manually run the garbage collector after every loop.
        We do not disable the automatic garbage collector, as a real python run would have it enabled,
        thus allowing to remove potentially unused memory.

    Example:
        >>> for _ in Profileit(10):
        ...     # benchmark code
        ...     pass

        >>> for p in Profileit(100):
        ...     # setup code
        ...     p.start()
        ...     # first part
        ...     p.split()
        ...     # second part
        ...     p.stop()

        >>> for p in Profileit(1000):
        ...     # setup code
        ...     with p:
        ...         # benchmark code
        ...         pass
    """
    def __init__(self, repeat=1, unit='Mb', label='memory', verbose=False, poll_interval=1e-3):
        self.repeat = repeat
        self.label = label
        self.unit = unit if unit.lower() in Profiler._units else 'Mb'
        self.verbose = verbose
        self.poll_interval = poll_interval
        self.values = defaultdict(list)

    def reset(self):
        self.values = defaultdict(list)

    def __iter__(self):
        if len(self.values):
            log.warning('self.values is not empty, consider calling reset between benchmarks')

        bg = Profiler(self.unit, self.label, False, self.poll_interval, {})
        fg = Profiler(self.unit, self.label, False, self.poll_interval, {})

        for i in range(self.repeat+1):
            bg.start()
            yield fg
            bg.stop()

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
                log.info('Loop %d: %.3f%s', i, self.values[self.label][-1], self.unit)

            fg.reset()
            fg.store = {}
            gc.collect()

        maxlen = max(len(k) for k in self.values.keys()) + 1
        for name, values in self.values.items():
            name += ':'
            if self.repeat > 1:
                log.info(
                    f'{name:<{maxlen}} worst {max(values):.3f}{self.unit} '
                    f'[mean {statistics.fmean(values):.3f} ± {statistics.stdev(values):.3f}{self.unit}]',
                )
            else:
                log.info(f'{name:<{maxlen}} worst {max(values):.3f}{self.unit}')
