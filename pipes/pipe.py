from __future__ import annotations
from typing import Any, Callable
import asyncio


class PipeBase:
    def __init__(self, *, max_size: int = -1, loop: asyncio.BaseEventLoop = None):
        self._loop = loop if loop else asyncio.get_event_loop()
        self._max_size = max_size
        self._next = self._loop.create_future()
        self._values = []

    def __aiter__(self):
        return PipeIterator(self)

    def __contains__(self, item):
        return item in self._values

    def __getitem__(self, index):
        return self._values[index]

    def __iter__(self):
        return PipeIterator(self)

    def __anext__(self):
        return self.next

    def __len__(self):
        return len(self._values)

    @property
    def max_size(self):
        return self._max_size

    @property
    def next(self) -> asyncio.Future[Any]:
        return self._next

    def close(self):
        self.next.cancel()

    def filter(
        self, predicate: Callable[[PipeBase, Any], bool], *, max_size: int = -1
    ) -> PipeFilteredView:
        return PipeFilteredView(self, predicate, max_size=max_size)

    def map(
        self, mapper: Callable[[PipeBase, Any], Any], *, max_size: int = -1
    ) -> PipeMappedView:
        return PipeMappedView(self, mapper, max_size=max_size)

    def iterate_first(self, limit: int) -> PipeIterator:
        return PipeIterator(self, limit=limit)

    def on_next(self, callback: Callable[[Any], None]):
        def caller(future):
            callback(future.result())

        self.next.add_done_callback(caller)

    def _push_value(self, value):
        if len(self) == self.max_size:
            self._values.pop(0)

        self._values.append(value)

    def _set_value(self, value):
        previous, self._next = self._next, self._loop.create_future()
        self._push_value(value)
        previous.set_result(value)


class Pipe(PipeBase):
    def push(self, value: Any):
        self._set_value(value)


class PipeView(PipeBase):
    def __init__(self, pipe: PipeBase, **kwargs):
        super().__init__(**kwargs)
        self._pipe = pipe

        self._watch()

    @property
    def pipe(self) -> PipeBase:
        return self._pipe

    def _receive_value(self, future: asyncio.Future):
        self._set_value(future.result())

    def _watch(self):
        def receive(future):
            self._watch()
            self._receive_value(future)

        self._pipe.next.add_done_callback(receive)


class PipeFilteredView(PipeView):
    def __init__(
        self, pipe: PipeBase, predicate: Callable[[PipeBase, Any], bool], **kwargs
    ):
        self._predicate = predicate

        super().__init__(pipe, **kwargs)

    def _receive_value(self, future: asyncio.Future):
        result = future.result()
        if self._predicate(self, result):
            self._set_value(result)


class PipeMappedView(PipeView):
    def __init__(
        self, pipe: PipeBase, mapper: Callable[[PipeBase, Any], Any], **kwargs
    ):
        self._mapper = mapper

        super().__init__(pipe, **kwargs)

    def _receive_value(self, future: asyncio.Future):
        result = future.result()
        mapped = self._mapper(self, result)
        self._set_value(mapped)


class PipeIterator:
    def __init__(self, pipe: PipeBase, *, limit=-1):
        self._current_index = 0
        self._limit = limit
        self._pipe = pipe

    def __aiter__(self):
        return self

    def __anext__(self):
        if self._limit <= 0 or self._current_index < self._limit:

            async def getter():
                if self._current_index >= len(self._pipe):
                    await self._pipe.next
                return self.get_next_value()

            return getter()

        raise StopAsyncIteration()

    def __iter__(self):
        return self

    def __next__(self):
        if (
            self._current_index >= len(self._pipe)
            or 0 < self._limit <= self._current_index
        ):
            raise StopIteration()

        return self.get_next_value()

    def get_next_value(self) -> Any:
        value = self._pipe[self._current_index]
        self._current_index += 1
        return value
