import asyncio
import gully


def test_stream_on_next():
    got_value = None

    def watch(value):
        nonlocal got_value
        got_value = value

    async def push(stream):
        stream.push(5)

    async def run():
        stream = gully.DataStream()
        stream.on_next(watch)
        await asyncio.sleep(0.1)
        await push(stream)

    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())

    assert got_value == 5


def test_stream_next():
    got_value = None

    async def watch(stream):
        nonlocal got_value
        got_value = await stream.next

    async def push(stream):
        stream.push(5)

    async def run():
        stream = gully.DataStream()
        loop.create_task(watch(stream))
        await asyncio.sleep(0.1)
        await push(stream)

    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())

    assert got_value == 5


def test_stream_iterate():
    got_value = []

    async def watch(stream):
        for value in stream:
            got_value.append(value)

    async def push(stream):
        stream.push(1)
        stream.push(2)
        stream.push(3)
        stream.push(4)
        await asyncio.sleep(0.1)
        stream.push(5)
        stream.close()

    async def run():
        stream = gully.DataStream()
        await asyncio.gather(push(stream), watch(stream))

    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())

    assert got_value == [1, 2, 3, 4]


def test_stream_async_iterate():
    got_value = []

    async def watch(stream):
        try:
            async for value in stream:
                got_value.append(value)
        except asyncio.exceptions.CancelledError:
            ...

    async def push(stream):
        stream.push(1)
        stream.push(2)
        stream.push(3)
        stream.push(4)
        await asyncio.sleep(0.1)
        stream.push(5)
        stream.close()

    async def run():
        stream = gully.DataStream()
        await asyncio.gather(push(stream), watch(stream))
        return stream

    loop = asyncio.new_event_loop()
    p = loop.run_until_complete(run())

    assert got_value == [1, 2, 3, 4, 5]


def test_stream_iterate_limit():
    got_value = []

    async def watch(stream):
        for value in stream.iterate_first(3):
            got_value.append(value)

    async def push(stream):
        stream.push(1)
        stream.push(2)
        stream.push(3)
        stream.push(4)
        await asyncio.sleep(0.1)
        stream.push(5)
        stream.close()

    async def run():
        stream = gully.DataStream()
        await asyncio.gather(push(stream), watch(stream))

    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())

    assert got_value == [1, 2, 3]


def test_stream_async_iterate_limit():
    got_value = []

    async def watch(stream):
        try:
            async for value in stream.iterate_first(3):
                got_value.append(value)
        except asyncio.exceptions.CancelledError:
            ...

    async def push(stream):
        stream.push(1)
        stream.push(2)
        stream.push(3)
        stream.push(4)
        await asyncio.sleep(0.1)
        stream.push(5)
        stream.close()

    async def run():
        stream = gully.DataStream()
        await asyncio.gather(push(stream), watch(stream))
        return stream

    loop = asyncio.new_event_loop()
    p = loop.run_until_complete(run())

    assert got_value == [1, 2, 3]
