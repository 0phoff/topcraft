# TOPCraft
Top Notch Python Debugging Tools.

This package contains some tools that I personally created and use when developping python code.
Feel free to use it, but beware that I might change the code in this package at a whim and do not respect any versioning whatsoever.
The best way would be to copy files or fork this repository if you want parts of it.


## Automatic Import
Python has a nifty feature called the `PYTHONSTARTUP` environment variable.
Set that variable to a file in your home directory and create that file:

```python
try:
    from top import *
except ImportError
    pass
```

You can now use everything from this package in any interactive python shell!
The try/except is there in case you create a virtual environment and did not install this package.
