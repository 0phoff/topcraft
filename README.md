# TOPCraft
Top Notch Python Debugging Tools.

This package contains some tools that I personally created and use when developping python code.
Feel free to use it, but beware that I might change the code in this package at a whim and do not respect any versioning whatsoever.
The best way would be to copy files or fork this repository if you want parts of it.

```bash
# Install latest
pip install git+https://github.com/0phoff/topcraft

# Install "safe" version
pip install git+https://github.com/0phoff/topcraft@v0.0.0
```


## Contents
All tools in this package are exported to the root level.
This means that if you `import top`, you can access everything as `top.*`.
Another way to use this package is to `from top import *`, so that all tools are available in the global scope.

> Note that you can use the built-in `help()` function to get more information about the arguments of each of these classes.

<dl>

<dt>log</dt>
<dd>

Standard python logging object with colorfull log levels.

</dd>
    
<dt>ToggleGC</dt>
<dd>

Disable/Enable/Toggle the garbage collector.

</dd>

<dt>Time</dt>
<dd>

Timing tool that allows you to measure time in 3 ways:
- start() - split() - stop() methods
- decorator
- context manager

</dd>

<dt>Timeit</dt>
<dd>

Tool to benchmark timings.
This tool uses the `Time` class to measure your code executions multiple times and report the best and average results.

</dd>

<dt>TimeTrend</dt>
<dd>

Tool to benchmark execution time trends.
This tools will yield from a `Timeit` class multiple times and return a tuple `num, timeit`.
This allows you to run code based on this number and thus measure execution speed for eg increasing array sizes.
Afterwards it will print the worst memory usage for each trend run.

</dd>

<dt>Mem</dt>
<dd>

Memory Profiling tool that allows you to measure memory usage in 3 ways:
- start() - split() - stop() methods
- decorator
- context manager

Note that memory profiling is not exact in python and you should take the results with a grain of salt!

</dd>

<dt>Memit</dt>
<dd>

Tool to benchmark memory usage.
This tool uses the `Mem` class to measure your code executions multiple times and report the worst and average results.

</dd>

<dt>MemTrend</dt>
<dd>

Tool to benchmark memory usage trends.
This tools will yield from a `Memit` class multiple times and return a tuple `num, memit`.
This allows you to run code based on this number and thus measure memory consumption for eg increasing array sizes.
Afterwards it will print the worst memory usage for each trend run.

</dd>

<dt>Profile</dt>
<dd>

Tool to measure either Time,Memory or do nothing depending on the `TOP_PROFILE` environment variable:
- TOP_PROFILE=time : Perform time measurement
- TOP_PROFILE=mem  : Perform memory measurement
- TOP_PROFILE=... or not set : Do nothing

</dd>

<dt>Profileit</dt>
<dd>

Tool to benchmark either Time,Memory or do nothing depending on the `TOP_PROFILE` environment variable:
- TOP_PROFILE=time : Perform time benchmark
- TOP_PROFILE=mem  : Perform memory benchmark
- TOP_PROFILE=... or not set : Do nothing

</dd>

<dt>ProfileTrend</dt>
<dd>

Tool to benchmark either Time or Memory trends or do nothing depending on the `TOP_PROFILE` environment variable:
- TOP_PROFILE=time : Perform time trend benchmark
- TOP_PROFILE=mem  : Perform memory trend benchmark
- TOP_PROFILE=... or not set : Do nothing

</dd>

<dt>meta</dt>
<dd>

A module containing few handy metaclasses and a function to combine them.  
Note that the functionality here is not exposed to the root level, as you would rarely need this in a script.

**WARNING:** This is probably useless for most of you out there, but I like to use complicated dangerous stuff...

- meta.AutoContextType : Allow to run class-based context manager without instantiation
- meta.AutoDecoratorType : Allow to run class-based decorator without instantiation
- meta.AutoIterType : Allow to run class-based iterator without instantiation
- meta.combine_types : combine various metaclasses together (technically allows to combine any class).

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
