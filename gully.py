"""Gully - Simple Observable Data Streams

The goal of Gully is to provide simple data streams that can be observed and manipulated without much fuss.

To use just create an instance of Gully and push data into the data stream using its `push` method. A gully stream can
be filtered by passing a single argument predicate function to the `filter` method, this will return a `FilteredGully`
which can be used just like a normal gully. It is also possible to map the values as they come into the gully by passing
a single argument mapping function to the `map` method which will return a `MappedGully`. Finally it is possible to
limit the number of items a gully will return by either setting the `limit` arg at instantiation or by calling the
`limit` method with the upper limit, it'll return a `Gully` object."""
from __future__ import annotations
from asyncio import Future
from inspect import isawaitable
from typing import Any, Awaitable, Callable, Optional, Union


Callback = Union[Awaitable, Callable]


class Gully:
    """Gully is a data stream. It can observe other data streams and it can be observed by either data streams or
    functions.

    It optionally takes a Gully object which it will observe. It also takes a limit, if it is positive the gully will
    only return that many values, if it is negative the gully will run so long as it is being passed values.

    All gully instances act as async iterators. So they can be used in an async for to observe future values that get
    pushed into the gully. When the gully stops it will end the iterator stopping the async for."""

    def __init__(self, stream: Optional[Gully] = None, limit: int = -1):
        self._next = Future()
        self._limit = limit

        if stream:
            self._observe_stream(stream)

    @property
    def done(self) -> bool:
        """Will be true if the gully has reached its limit."""
        return self._next.done()

    @property
    def next(self) -> FutureView:
        """A future for the next value that will be pushed into the gully. This future will resolve to the next value.
        It is a `FutureView` so cannot be modified or cancelled."""
        return FutureView(self._next)

    def filter(self, predicate: Callable, limit: int = -1) -> FilteredGully:
        """Creates a filtered gully for all values passed into the gully."""
        return FilteredGully(predicate, self, limit)

    def limit(self, limit: int) -> Gully:
        """Creates a gully that is limited to `limit` values."""
        return Gully(self, limit)

    def map(self, mapping: Callable, limit: int = -1):
        """Creates a mapped gully that maps all values passed into the gully."""
        return MappedGully(mapping, self, limit)

    def push(self, value: Any):
        """Pushes a value into the gully. If the gully is done/stopped nothing will happen."""
        if self.done:
            return

        if self._limit > 0:
            self._limit -= 1

        old, self._next = self._next, Future()
        if self._limit == 0:
            self._next.cancel()

        old.set_result(value)

    def stop(self):
        """Stops the gully by cancelling the next value's future."""
        self._next.cancel()

    def watch(self, callback: Callback) -> Observer:
        """Adds a callback (either a callable or coroutine) that will be run everytime a value is pushed into the gully."""
        return Observer(callback, self)

    def _observe_stream(self, stream: Gully):
        def observer(future: Future):
            if future.cancelled():
                self._next.cancel()
            else:
                self.push(future.result())
                self._observe_stream(stream)

        stream.next.add_done_callback(observer)

    def __aiter__(self):
        return self

    def __anext__(self):
        if self.done:
            raise StopAsyncIteration()
        return IterationFuture(self._next)


class FilteredGully(Gully):
    """A simple filterable gully. It expects a callable that takes a single argument and that returns a boolean. The
    callable will be passed each value that's being pushed into the gully and if it returns `True` the value will be
    allowed, if it returns `False` the value will not be pushed and will be ignored."""

    def __init__(
        self,
        predicate: Callable[[Any], bool],
        stream: Optional[Gully] = None,
        limit: int = 0,
    ):
        super().__init__(stream, limit)
        self._predicate = predicate

    def push(self, value: Any):
        """Pushes a value into the gully only if the predicate returns `True` for the value."""
        if self._predicate(value):
            super().push(value)


class MappedGully(Gully):
    """A simple mapping gully. It expects a callable that takes a single argument and that any value. The callable will
    be passed each value that's being pushed into the gully and the value the callable returns will be what gets pushed.
    """

    def __init__(
        self,
        mapping: Callable[[Any], Any],
        stream: Optional[Gully] = None,
        limit: int = 0,
    ):
        super().__init__(stream, limit)
        self._mapping = mapping

    def push(self, value: Any):
        """Pushes a value into the gully that has been mapped by the mapping callable."""
        super().push(self._mapping(value))


class FutureView:
    """A view into a future. This prevents setting exceptions and results as well as cancelling the future being viewed."""

    def __init__(self, future: Future):
        self.__future = future

    def cancel(self, *args) -> bool:
        raise PermissionError()

    def set_exception(self, *args) -> None:
        raise PermissionError()

    def set_result(self, *args) -> None:
        raise PermissionError()

    def __getattr__(self, item: str):
        if not item.startswith("_"):
            return getattr(self.__future, item)


class IterationFuture(Future):
    """A proxy future that converts a cancellation into a `StopAsyncIteration` exception to stop async for loops waiting
    on the future."""

    def __init__(self, future: Future, **kwargs):
        super().__init__(**kwargs)
        future.add_done_callback(self._future_done)

    def _future_done(self, future: Future):
        if future.cancelled():
            self.set_exception(StopAsyncIteration())
        else:
            self.set_result(future.result())


class Observer:
    """A simple observer that calls a callback each time a new value gets added to a gully. The callback can be either a
    function or a coroutine."""

    def __init__(self, callback: Callback, stream: Gully):
        self._callback = callback
        self._stream = stream

        self._setup()

    def stop(self):
        """Stops the observer from watching for new values."""
        self._stream.next.remove_done_callback(self._run)

    def _run(self, future: Future):
        self._setup()
        result = self._callback(future.result())
        if isawaitable(result):
            future.get_loop().create_task(result)

    def _setup(self):
        self._stream.next.add_done_callback(self._run)
