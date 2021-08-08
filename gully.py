"""Gully - Simple Observable Data Streams

The goal of Gully is to provide simple data streams that can be observed and manipulated without much fuss.

You can push values into a gully and it'll pass that value down to any observers. It'll also store the value in the
gully's history. The values pushed into the gully can be filtered and mapped. Filter and mapping functions should take a
single value argument. Filter functions should return True to keep the value or False to have it removed. Mapping
functions return the new mapped value or the value if it wasn't changed. Filter and map functions will be added to a
pipeline that will execute the functions in the order that they were added. Maps and filters can be added when creating
the gully instance or later on by using the add_filters and add_mappings methods.

It's also possible to branch a gully by using it's map and filter methods. This will create a new gully instance that
captures anything pushed into the original gully.

The gully watch method returns an observer that can be used to control if the observer should continue watching. Using
the return observer object it is possible start and stop watching any number of times."""
from __future__ import annotations

import asyncio
from collections import deque, UserList
from functools import partial
from inspect import isawaitable
from typing import Any, Awaitable, Callable, Optional, Sequence, Union


Callback = Callable[[Any], Awaitable[Any]]


class NotAFilterMatch(Exception):
    ...


class Gully:
    """The core gully object. It tracks the push history using a deque that inserts the newest push at the 0 index. It
    makes the history viewable as a read only HistoryView object.

    Parameters
    *watching: One or more gullies that this gully should aggregate.
    filters: This should be a sequence of coroutines that take a single value argument and return a bool.
    mappings: This should be a sequences of coroutines that take a single value argument and return the new value to use
              in its place, or the original value if it is unchanged.
    max_size: The maximum size of the push history. Values less than 1 will cause the history to be unlimited.
    loop: The asyncio event loop that the gully should use for calling observers."""

    __slots__ = ("_history", "_loop", "_pipeline", "_observers")

    def __init__(
        self,
        *watching: Gully,
        filters: Sequence[Union[Callback, Callable[[Any], Any]]] = tuple(),
        mappings: Sequence[Union[Callback, Callable[[Any], Any]]] = tuple(),
        max_size: int = -1,
        loop: Optional[asyncio.AbstractEventLoop] = None
    ):
        self._history = deque(maxlen=max_size > 0 and max_size or None)
        self._loop = loop or asyncio.get_running_loop()
        self._pipeline = Pipeline()
        self._observers = set()

        self.add_filter(*filters)
        self.add_mapping(*mappings)

        for gully in watching:
            gully.watch(self.push)

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """The event loop that the gully should use for calling observers."""
        return self._loop

    @property
    def history(self) -> HistoryView:
        """The most recent push history sorted most recent to least recent. This uses a HistoryView to protect against
        modifications to the history list."""
        return HistoryView(self._history)

    @property
    def pipeline(self) -> Pipeline:
        """The gully's pipeline object. This allows lower level control of the pipeline if needed. Push will only ever
        call the pipeline's run method with 1 argument, so anything added to the pipeline must support only receiving a
        single argument."""
        return self._pipeline

    async def push(self, item: Any):
        """Pushes an item into the gully history. The item will be passed through the filter and mapping pipeline and
        the final result will be added to the history and will be sent to all observers."""
        try:
            value = await self._pipeline.run(item)
        except NotAFilterMatch:
            return
        else:
            self._history.appendleft(value)
            for observer in self._observers:
                self.loop.create_task(observer(value))

    def filter(
        self, *predicates: Union[Callback, Callable[[Any], Any]], max_size: int = -1
    ) -> Gully:
        """Branches the gully into a new gully which uses the given filter predicates. The branched gully can have a
        custom max_size set."""
        return Gully(self, filters=predicates, max_size=max_size)

    def map(
        self, *mappings: Union[Callback, Callable[[Any], Any]], max_size: int = -1
    ) -> Gully:
        """Branches the gully into a new gully which uses the given mapping callbacks. The branched gully can have a
        custom max_size set."""
        return Gully(self, mappings=mappings, max_size=max_size)

    def add_filter(self, *predicates: Union[Callback, Callable[[Any], Any]]):
        """Adds the given filter predicates to the gully pipeline. These cannot be removed, use the filter method to
        create a new gully that has the desired filter predicates if they need to be disabled later.

        This wraps each filter predicate in a function that will raise NotAFilterMatch if the filter predicate returns
        False. This will cause the pipeline to stop and push will ignore the current item, not adding it to the history
        and not calling the observers."""

        def filter_wrapper(predicate, item):
            if not predicate(item):
                raise NotAFilterMatch()
            return item

        self._pipeline.add(
            *(partial(filter_wrapper, predicate) for predicate in predicates)
        )

    def add_mapping(self, *mappings: Union[Callback, Callable[[Any], Any]]):
        """Adds the given mapping callbacks to the gully pipeline. These cannot be removed, use the map method to create
        a new gully that has the desired mapping callbacks if they need to be disabled later."""
        self._pipeline.add(*mappings)

    def watch(self, callback: Callback) -> Observer:
        """Adds an observer callback to the gully. When new values are successfully pushed into the gully the observer
        will be called with the new value."""
        observer = callback
        if not isinstance(callback, Observer):
            observer = Observer(
                callback,
                partial(self._observers.add, callback),
                partial(self._observers.remove, callback),
            )
        observer.enable()
        return observer

    def stop_watching(self, callback: Union[Callback, Observer]):
        """Removes an observer from the gully. This will accept either the original callback or an observer object that
        wraps that callback."""
        self._observers.remove(callback)


class HistoryView(UserList):
    """A readonly view for lists."""

    def __setitem__(self, key, value):
        raise TypeError(
            "'{type(self).__name__}' object does not support item assignment"
        )


class Observer:
    """Simple wrapper for callback coroutines. This allows the observer to be enabled or disabled the observer. The
    observer must be provided a start function that enables the callback to observer new events and a stop function that
    disables it.

    This can be used as a stand-in for the callback in sets/dictionaries keys or when stopping a watcher on a gully
    object."""

    __slots__ = ("_callback", "_start", "_stop")

    def __init__(self, callback, start, stop):
        self._callback = callback
        self._start = start
        self._stop = stop

    def enable(self):
        """Enables the observer by calling the start function it was provided."""
        self._start()

    def disable(self):
        """Disables the observer by calling the stop function it was provided."""
        self._stop()

    def __eq__(self, other):
        return other == self._callback

    def __hash__(self):
        return hash(self._callback)


class Pipeline:
    """A simple action pipeline that allows steps to be run in order."""

    def __init__(self):
        self._steps = []

    def __call__(self, *args, **kwargs) -> Awaitable[Any]:
        """Calls the pipeline's run method. It must be awaited."""
        return self.run(*args, **kwargs)

    def add(self, *steps):
        """Adds any number of steps to the pipeline."""
        self._steps.extend(steps)

    async def run(self, item: Any, *args, **kwargs) -> Any:
        """Runs the pipeline. It will replace the first argument passed with the return from prior steps."""
        value = item
        for step in self._steps:
            value = step(value, *args, **kwargs)
            if isawaitable(value):
                value = await value
        return value
