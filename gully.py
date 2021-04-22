"""Gully - Simple Observable Data Streams

The goal of Gully is to provide simple data streams that can be observed and manipulated without much fuss.

To use just create an instance of Gully and push data into the data stream using its `push` method. A gully stream can
be filtered by passing a single argument predicate function to the `filter` method, this will return a `FilteredGully`
which can be used just like a normal gully. It is also possible to map the values as they come into the gully by passing
a single argument mapping function to the `map` method which will return a `MappedGully`. Finally it is possible to
limit the number of items a gully will return by either setting the `limit` arg at instantiation or by calling the
`limit` method with the upper limit, it'll return a `Gully` object."""
from __future__ import annotations

import asyncio
from asyncio import Future
from typing import Any, Awaitable, Callable, Union


Callback = Union[Awaitable, Callable]


class Gully:
    """Gully is a data stream. It can observe other data streams and it can be observed by either data streams or
    functions.

    It optionally takes a Gully object which it will observe. It also takes a limit, if it is positive the gully will
    only return that many values, if it is negative the gully will run so long as it is being passed values.

    All gully instances act as async iterators. So they can be used in an async for to observe future values that get
    pushed into the gully. When the gully stops it will end the iterator stopping the async for."""

    def __init__(self, limit: int = -1):
        self._next = Future()
        self._limit = limit
        self._observers = set()

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
        f = FilteredGully(predicate, limit)
        self._watch(f)
        return f

    def limit(self, limit: int) -> Gully:
        """Creates a gully that is limited to `limit` values."""
        l = Gully(limit)
        self._watch(l)
        return l

    def map(self, mapping: Callable, limit: int = -1):
        """Creates a mapped gully that maps all values passed into the gully."""
        m = MappedGully(mapping, limit)
        self._watch(m)
        return m

    def push(self, value: Any):
        """Pushes a value into the gully. If the gully is done/stopped nothing will happen."""
        if self.done:
            return

        if self._limit > 0:
            self._limit -= 1

        old, self._next = self._next, Future()
        old.set_result(value)
        self._push(value)

        if self._limit == 0:
            self.stop()

    def stop(self):
        """Stops the gully by cancelling the next value's future."""
        self._next.cancel()
        for observer in self._observers:
            observer.stop()

    def watch(self, callback: Callback) -> Observer:
        """Adds a callback (either a callable or coroutine) that will be run everytime a value is pushed into the gully."""
        observer = Observer(callback)
        self._watch(observer)
        return observer

    def _watch(self, observer: Union[Observer, Gully]):
        self._observers.add(observer)

    def _push(self, value: Any):
        for observer in self._observers.copy():
            if observer.done:
                self._observers.remove(observer)
            else:
                observer.push(value)

    def __aiter__(self):
        observer = ObserverIterator()
        self._observers.add(observer)
        return observer


class FilteredGully(Gully):
    """A simple filterable gully. It expects a callable that takes a single argument and that returns a boolean. The
    callable will be passed each value that's being pushed into the gully and if it returns `True` the value will be
    allowed, if it returns `False` the value will not be pushed and will be ignored."""

    def __init__(
        self,
        predicate: Callable[[Any], bool],
        limit: int = 0,
    ):
        super().__init__(limit)
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
        limit: int = 0,
    ):
        super().__init__(limit)
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


class Observer:
    """A simple observer that calls a callback each time a new value gets added to a gully. The callback can be either a
    function or a coroutine."""

    def __init__(self, callback: Callback, *, loop=None):
        self._queue = [asyncio.Future()]
        self.callback = callback
        (loop if loop else asyncio.get_event_loop()).create_task(self._watch())

    @property
    def done(self) -> bool:
        return self._queue[-1].done()

    def stop(self):
        self._queue[-1].cancel()

    def push(self, value):
        self._queue.append(asyncio.Future())
        self._queue[-2].set_result(value)

    async def _watch(self):
        while not self._queue[-1].done():
            future = self._queue[-1]
            value = await future
            self._queue.remove(future)
            self.callback(value)


class ObserverIterator(Observer):
    """A simple observer that calls a callback each time a new value gets added to a gully. The callback can be either a
    function or a coroutine."""

    def __init__(self, *, loop=None):
        super().__init__(None, loop=loop)

    def stop(self):
        self._queue[-1].set_exception(StopAsyncIteration)
        super().stop()

    async def __anext__(self):
        value = await self._queue[-1]
        return value

    async def _watch(self):
        return
