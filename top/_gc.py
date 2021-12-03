###########################
# Garbage Collection Code #
###########################
import gc
import logging
from functools import wraps

from ._meta import AutoContextType, AutoDecoratorType, combine_types

__all__ = ['ToggleGC']
log = logging.getLogger(__name__)


class ToggleGC(metaclass=combine_types(AutoContextType, AutoDecoratorType)):
    """
    Toggle Garbage Collection.
    This class can be used as a context manager or function decorator.
    If you do not need to change the default arguments, you can omit the braces for "creating the object".

    Args:
        target (bool or None, optional):
            Whether to enable or disable the GC; Default False

    Note:
        If you set the `target` argument to None, we simply toggle the garbage collection state.

    Example:
        >>> with TogleGC:
        ...     # Code inside has GC disabled
        ...     pass

        >>> @ToggleGC(None)
        ... def func():
        ...     # Code inside will have GC toggled
        ...     pass
    """
    def __init__(self, target=False):
        self.target = target
        self.revert = False

    def _start(self):
        status = gc.isenabled()

        if status and not self.target:
            gc.disable()
            self.revert = (True, True)
            log.debug('Garbage Collection Disabled')
        elif not status and self.target in (None, True):
            gc.enable()
            self.revert = (True, False)
            log.debug('Garbage Collection Enabled')

    def _stop(self):
        revert, value = self.revert
        self.revert = None

        if revert:
            if value:
                gc.enable()
                log.debug('Garbage Collection Enabled')
            else:
                gc.disable()
                log.debug('Garbage Collection Disabled')

    def __call__(self, fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            with(self):
                return fn(*args, **kwargs)
        return inner

    def __enter__(self):
        self._start()

    def __exit__(self, ex_type, ex_value, trace):
        self._stop()
        return False
