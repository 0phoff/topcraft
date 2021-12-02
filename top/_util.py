###################################
# Utilities that are not exported #
###################################
import logging
from collections import deque

__all__ = ['AutoDecoratorContextManagerType']
log = logging.getLogger(__name__)


class AutoDecoratorContextManagerType(type):
    """
    This metaclass has 2 purposes:
        - Allow to use a class-based decorator without instantiation
        - Allow to use a class-based contextmanager without instantiation

    It is probably overkill and the only reason I am using it is because I can.

    Example:
        >>> class CustomClass(metaclass=AutoDecoratorContextManagerType):
        ...     # TODO: implement __init__ and provide default values for each argument!
        ...     # TODO: implement __call__ to create your decorator
        ...     # TODO: implement __enter__ and __exit__ to create your contextmanager
        ...     pass

        >>> # Use as decorator, without creating a class instance (no braces)
        >>> @CustomClass
        ... def func():
        ...     pass

        >>> # Use as contextmanager, without creating a class instance (no braces)
        >>> with CustomClass:
        ...     pass
    """
    def __init__(cls, *args, **kwargs):
        cls.__instances = deque()
        super().__init__(*args, **kwargs)

    def __call__(cls, *args, **kwargs):
        if len(args) == 1 and callable(args[0]):
            obj = super().__call__()
            return obj(args[0])
        return super().__call__(*args, **kwargs)

    def __enter__(cls):
        obj = cls()
        cls.__instances.append(obj)
        return obj.__enter__()

    def __exit__(cls, ex_type, ex_value, trace):
        obj = cls.__instances.pop()
        return obj.__exit__(ex_type, ex_value, trace)
