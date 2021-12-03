###################################
# Utilities that are not exported #
###################################
import logging
from collections import deque

__all__ = ['AutoContextType', 'AutoDecoratorType', 'AutoIterType', 'combine_types']
log = logging.getLogger(__name__)
types = {}


class AutoDecoratorType(type):
    """
    This metaclass allows to use class-based decorators without actually instantiating them.
    When used, it will automatically create your object (with default args) and wrap your function.

    Note:
        This metaclass will not work for decorator classes that take a single callable argument during initialization.

    Example:
        >>> class CustomClass(metaclass=AutoDecoratorType):
        ...     # TODO: implement __init__ and provide default values for each argument!
        ...     # TODO: implement __call__ to create your decorator
        ...     pass

        >>> # Use as decorator, without creating a class instance (no braces)
        >>> @CustomClass
        ... def func():
        ...     pass

    """
    def __call__(cls, *args, **kwargs):
        if len(args) == 1 and callable(args[0]):
            obj = cls()
            return obj(args[0])
        return super().__call__(*args, **kwargs)


class AutoContextType(type):
    """
    This metaclass allows to use class-based context managers without actually instantiating them.
    When used, it will automatically create your object (with default args) and start the context manager.

    Example:
        >>> class CustomClass(metaclass=AutoContextType):
        ...     # TODO: implement __init__ and provide default values for each argument!
        ...     # TODO: implement __enter__ and __exit__ to create your contextmanager
        ...     pass

        >>> # Use as contextmanager, without creating a class instance (no braces)
        >>> with CustomClass:
        ...     pass
    """
    def __init__(cls, *args, **kwargs):
        cls.__instances = deque()
        super().__init__(*args, **kwargs)

    def __enter__(cls):
        obj = cls()
        cls.__instances.append(obj)
        return obj.__enter__()

    def __exit__(cls, ex_type, ex_value, trace):
        obj = cls.__instances.pop()
        return obj.__exit__(ex_type, ex_value, trace)


class AutoIterType(type):
    """
    This metaclass allows to use class-based iterators without actually instantiating them.
    When used, it will automatically create your object (with default args) and return your iterator.

    Example:
        >>> class CustomClass(metaclass=AutoIterType):
        ...     # TODO: implement __init__ and provide default values for each argument!
        ...     # TODO: implement __iter__to create your iterator
        ...     pass

        >>> # Use as iterator, without creating a class instance (no braces)
        >>> generator = iter(CustomClass)
        >>> for values in CustomClass:
        ...     pass
    """
    def __iter__(cls):
        obj = cls()
        return obj.__iter__()


def combine_types(*args):
    """
    This function allows to combine 2 or more metaclasses together.
    It will cache this result so fetching the same combined metaclass multiple times
    will not result in a different class construction.

    Args:
        *args (metaclasses): Metaclasses to combine

    Note:
        We rely on class.__name__ to uniquely identify types.
        Beware that if you have a type in another module with the same name, this will break everything.

    Example:
        >>> # Combine AutoContext and AutoIter
        >>> class CustomClass(metaclass=combine_types(AutoContextType, AutoIterType):
        ...     pass
    """
    global types

    name = ''.join(a.__name__ for a in args)
    if name not in types:
        types[name] = type(name, args, {})
    return types[name]
