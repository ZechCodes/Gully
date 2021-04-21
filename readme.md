# Gully

Gully is a simple framework for manipulating asynchronous streams of data.

## Installation
```shell
pip install gully
```

## Usage
```python
import gully

async def monitor_stream_using_iterator(stream: gully.Gully):
    async for item in stream:
        print(item)

async def monitor_stream_using_future(stream: gully.Gully):
    while not stream.done:
        item = await stream.next
        print(item)

async def monitor_stream_observer(stream: gully.Gully):
    def observer(item):
        print(item)
        
    stream.watch(observer)

data_stream = gully.Gully()
filtered = data_stream.filter(lambda item: item == "foobar")
mapped = filtered.map(lambda item: item.upper())
```
## Documentation

### gully.Gully(stream: Gully = None, limit: int = -1)

Gully is a data stream. It can observe other data streams and it can be observed by either data streams or functions.

It optionally takes a Gully object which it will observe. It also takes a limit, if it is positive the gully will only return that many values, if it is negative the gully will run so long as it is being passed values.

All gully instances act as async iterators. So they can be used in an async for to observe future values that get pushed into the gully. When the gully stops it will end the iterator stopping the async for.

- `property Gully.done: bool` Is the gully done, either because it reached its limit or was stopped

- `property Gully.next: gully.FutureView` The future that will receive the next value that is pushed into the data stream. This future will change with every pushed value, it will be cancelled if the stream is stopped or reaches its limit. It is a `FutureView` to prevent alterations to the underlying future. 

**`method Gully.push(value: Any)`**

Pushes a value into the data stream.

**`method DataStream.stop()`**

Stops the stream and cancels the next future stopping all watchers.

**`method Gully.watch(callback: Callable[[Any], None])`**

Registers a function to be called whenever a new value is pushed into the stream. The function may also be a coroutine.

**`method Gully.filter(predicate: Callable[[Any], bool], limit: int = -1) -> FilteredGully`**

Creates a gully that only pushes values that the predicate function allows. The predicate function should return `True` for any value that should be allowed into the stream.

**`method Gully.map(mapping: Callable[[Any], Any], limit: int = -1) -> MappedGully`**

Creates a gully that passes every value pushed to the stream into the mapping function, the returned value will be pushed into the gully.

### gully.FilteredGully(gully.Gully)

A simple filterable gully that inherits from `Gully`. It expects a callable that takes a single argument and that returns a boolean. The callable will be passed each value that's being pushed into the gully and if it returns `True` the value will be allowed, if it returns `False` the value will not be pushed and will be ignored.

### gully.MappedGully

A simple mapping gully that inherits from `Gully`. It expects a callable that takes a single argument and that any value. The callable will be passed each value that's being pushed into the gully and the value the callable returns will be what gets pushed.
