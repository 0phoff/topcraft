# TOPCraft
Top Notch Python Debugging Tools.

This package contains some tools that I personally created and use when developping python code.
Feel free to use it, but beware that I might change the code in this package at a whim and do not respect any versioning whatsoever.
The best way would be to copy files or fork this repository if you want parts of it.


## Contents
All tools in this package are exported to the root level.
This means that if you `import top`, you can access everything as `top.*`.
Another way to use this package is to `from top import *`, so that all tools are available in the global scope.

<dl>

<dt>log</dt>
<dd>

Standard python logging object with colorfull log levels.

</dd>
    
<dt>ToggleGC</dt>
<dd>

Disable/Enable/Toggle the garbage collector.

</dd>

<dt>Timer</dt>
<dd>

Timing tool that allows you to measure time in 3 ways:
- start() - split() - stop() methods
- decorator
- context manager

</dd>

<dt>Timeit</dt>
<dd>

Tool to benchmark timings.
This tool use the `Timer` to measure your code executions multiple times and report the best and average results.

</dd>

<dt>Profiler</dt>
<dd>

Profiler tool that allows you to measure memory usage in 3 ways:
- start() - split() - stop() methods
- decorator
- context manager

Note that memory profiling is not exact in python and you should take the results with a grain of salt!

</dd>

<dt>Profileit</dt>
<dd>

Tool to benchmark memory usage.
This tool use the `Profiler` to measure your code executions multiple times and report the worst and average results.

</dd>

</dl>

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
