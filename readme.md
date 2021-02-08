# Gully

Gully is a simple framework for manipulating streams of data. It provides methods for asynchronous & synchronous access to the streams.

## Installation
```shell
pip install gully
```

## Usage
```python
import gully

async def monitor_stream_using_iterator(stream: gully.DataStream):
    async for item in stream:
        print(item)

async def monitor_stream_using_future(stream: gully.DataStream):
    while not stream.next.done():
        item = await stream.next
        print(item)
        

data_stream = gully.DataStream()
filtered = data_stream.filter(lambda stream, item: item == "foobar")
mapped = filtered.map(lambda stream, item: item.upper())
```
## Documentation

### gully.DataStream(max_size: int = -1, loop: asyncio.Loop = None)

Provides the interface into the data stream. It offers both iterable and async iterable functionality, it also has item getters for accessing history. 

The data stream will cache past values up to `max_size` items, or unlimited if `max_size` is less than 1. These values can be accessed using get item (e.g. `stream[1]`), `len(stream)` will return the total number and items cached, and `value in stream` will tell you if a value is in the data stream.

Iterating through the data stream will go through the value cache from oldest to newest. Using an async iterator will go through the cache from oldest to newest and then will await new values.

- `property DataStream.max_size: int` The maximum size set for the data stream cache.

- `property DataStream.next: asyncio.Future` The future that will receive the next value that is pushed into the data stream. This future will change with every pushed value, it will be cancelled if the stream is closed. 

**`method DataStream.push(value: Any)`**

Pushes a value into the data stream.

**`method DataStream.close()`**

Closes the stream and cancels the next future stopping all watchers whether created synchronously, asynchronously, or through an iterator.

**`method DataStream.on_next(callback: Callable[[DataStreamBase, Any], None])`**

Registers a function to be called when the next future is set. The callback will be passed the data stream it was registered on and the value that was pushed.

**`method DataStream.iterate_first(limit: int) -> DataStreamIterator`**

Gets an iterator that will only yield at most `limit` items. This iterator can be used either synchronously or asynchronously, only an async iterator will wait for new values to be pushed. This will always start at the oldest item in the cache.

**`method DataStream.filter(predicate: Callable[[DataStreamBase, Any], bool], max_size: int = -1) -> DataStreamFilteredView`**

Creates a data stream view that only receives values that the predicate function allows. The predicate function should return `True` for any value that should be allowed into the stream.

**`method DataStream.map(mapper: Callable[[DataStreamBase, Any], Any], max_size: int = -1) -> DataStreamMappedView`**

Creates a data stream view that passes every value pushed to the stream into the mapping function, the returned value will be pushed into the data stream view.

### gully.DataStreamFilteredView

Functions like a normal DataStream but it monitors other streams and only pushes values to itself that pass the predicate function's conditions. The cache history begins when it is created and will not have access to older values from the stream it is monitoring.

### gully.DataStreamMappedView

Functions like a normal DataStream but it monitors other streams and passes the new values through a mapping function before pushing them to itself. The cache history begins when it is created and will not have access to older values from the stream it is monitoring.
