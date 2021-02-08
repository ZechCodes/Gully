# Pipes

Pipes is a simple framework for manipulating streams of data. It provides methods for asynchronous & synchronous access to the streams.

## Installation
```shell
pip install pipes
```

## Usage
```python
import pipes

async def monitor_pipe_using_iterator(pipe: pipes.Pipe):
    async for item in pipe:
        print(item)

async def monitor_pipe_using_future(pipe: pipes.Pipe):
    while not pipe.next.done():
        item = await pipe.next
        print(item)
        

data_pipe = pipes.Pipe()
filtered = data_pipe.filter(lambda pipe, item: item == "foobar")
mapped = filtered.map(lambda pipe, item: item.upper())
```
## Documentation

### pipes.Pipe(max_size: int = -1, loop: asyncio.Loop = None)

Provides the interface into the data stream. It offers both iterable and async iterable functionality, it also has item getters for accessing history. 

The pipe will cache past values up to `max_size` items, or unlimited if `max_size` is less than 1. These values can be accessed using get item (e.g. `pipe[1]`), `len(pipe)` will return the total number and items cached, and `value in pipe` will tell you if a value is in the pipe.

Iterating through the pipe will go through the value cache from oldest to newest. Using an async iterator will go through the cache from oldest to newest and then will await new values.

`property Pipe.max_size: int`
The maximum size set for the pipe cache.

`property next: asyncio.Future`
The future that will receive the next value that is pushed into the pipe. This future will change with every pushed value, it will be cancelled if the pipe is closed. 

**`Pipe.push(value: Any)`**

Pushes a value into the pipe.

**`Pipe.close()`**

Closes the pipe and cancels the next future stopping all watchers whether created synchronously, asynchronously, or through an iterator.

**`Pipe.on_next(callback: Callable[[PipeBase, Any], None])`**

Registers a function to be called when the next future is set. The callback will be passed the pipe it was registered on and the value that was pushed.

**`Pipe.iterate_first(limit: int) -> PipeIterator`**

Gets an iterator that will only yield at most `limit` items. This iterator can be used either synchronously or asynchronously, only an async iterator will wait for new values to be pushed. This will always start at the oldest item in the cache.

**`Pipe.filter(predicate: Callable[[PipeBase, Any], bool], max_size: int = -1) -> PipeFilteredView`**

Creates a pipe view that only receives values that the predicate function returns `True` for.

**`Pipe.map(mapper: Callable[[PipeBase, Any], Any], max_size: int = -1) -> PipeMappedView`**

Creates a pipe view that passes every value pushed through the mapping function and pushes that value into the mapped pipe view.

### pipes.PipeFilteredView

Functions like a normal Pipe but it monitors other pipes and only pushes values to itself that pass the predicate function's conditions. The cache history begins when it is created and will not have access to older values from the pipe it is monitoring.

### pipes.PipeMappedView

Functions like a normal Pipe but it monitors other pipes and passes the new values through a mapping function before pushing them to itself. The cache history begins when it is created and will not have access to older values from the pipe it is monitoring.
