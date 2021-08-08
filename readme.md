# Gully

[![PyPI version](https://img.shields.io/pypi/v/gully?color=informational&style=flat-square)](https://pypi.python.org/pypi/gully/)
[![PyPI license](https://img.shields.io/pypi/l/gully?style=flat-square&color=orange)](https://lbesson.mit-license.org/)

Gully is a simple framework for manipulating asynchronous streams of data.

## Installation
```shell
pip install gully
```

## Usage
```python
import asyncio
import gully

async def observer(item):
    print(item)
    
async def main():
    stream = gully.Gully()
    stream.watch(observer)
    stream.add_filter(lambda item: item == "foobar")
    stream.add_mapping(lambda item: item.upper())
    await stream.push("foobar")
    await stream.push("baz")
    await stream.push("foobar")

asyncio.run(main())
```
*Output*
```
FOOBAR
FOOBAR
```
## Documentation

### gully.Gully(watch: Sequence[Gully] = None, *, filters: Sequence[Callable], mappings: Sequence[Callable], max_size: int = -1, loop: EventLoop = None)

Gully is a stream. It can observe other gullies, and it can be observed by coroutines. Any number of gullies can be passed as args, the new gully will observe them to aggregate their pushes. By default gullies will retain an unlimited history of their pushes, this can be changed by setting the `max_size` keyword arg to any value greater than 0. 

- `property Gully.loop: asyncio.AbstractEventLoop` This is the loop that the gully will use to run observers.

- `property Gully.history: gully.HistoryView` The current history of pushes to the gully. This is a view that cannot be set to. It is restricted by the `max_size` setting that was given to the gully.

- `property Gully.pipeline: gully.Pipeline` The pipeline that is run when pushing a new item into the gully. The gully will only ever call the pipeline with a single argument, so all steps added to the pipeline must support only receiving a single argument.

**`method Gully.push(value: Any)`**

Pushes a value into the gully. This will run the pipeline to map and filter the value. It will only add it to the history and call the observers if a filter doesn't reject the value.

**`method Gully.watch(callback: Callable[[Any], Awaitable[None]])`**

Registers a coroutine to observe new values that are pushed into the gully.

**`method Gully.filter(*predicates: Callable[[Any], bool], max_size: int = -1) -> Gully`**

Branches the gully into a new gully which uses the given filter predicates. The branched gully can have a custom `max_size` set.

**`method Gully.map(mapping: Callable[[Any], Any], max_size: int = -1) -> Gully`**

Branches the gully into a new gully which uses the given mapping callbacks. The branched gully can have a custom `max_size` set.

**`method Gully.add_filter(*predicates: Callable[[Any], Any])`**

Adds the given filter predicates to the gully pipeline. These cannot be removed, use the filter method to create a new gully that has the desired filter predicates if they need to be disabled later.

This wraps each filter predicate in a function that will raise `NotAFilterMatch` if the filter predicate returns `False`. This will cause the pipeline to stop and push will ignore the current item, not adding it to the history and not calling the observers.

**`method Gully.add_mapping(*mappings: Callable[[Any], Any])`**

Adds the given mapping callbacks to the gully pipeline. These cannot be removed, use the map method to create a new gully that has the desired mapping callbacks if they need to be disabled later.

**`method Gully.stop_watching(callback: Union[Callable, Observer])`**

Removes an observer from the gully. This will accept either the original callback, or an observer object that wraps that callback.

### gully.Observable(gully.Gully)

Simple wrapper for callback coroutines. This allows the observer to be enabled or disabled. The observer must be provided a start function that enables the callback to observer new events, and a stop function that disables it.

This can be used as a stand-in for the callback in sets/dictionaries keys or when stopping a watcher on a gully object.

### gully.Pipeline

A simple action pipeline that allows steps to be run in order.

**`method Pipeline.add(*steps: Callable[[Any], Any])`**

Adds any number of steps to the pipeline.

**`method Pipeline.run(item: Any, *args, **kwargs)`**

Runs the pipeline. It will replace the first argument passed with the return from prior steps.
