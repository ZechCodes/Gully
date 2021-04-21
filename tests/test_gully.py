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
        stream = gully.Gully()
        stream.watch(watch)
        await asyncio.sleep(0.1)
        await push(stream)

    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())

    assert got_value == 5


def test_stream_async_for():
    got_value = []

    async def watch(stream):
        async for value in stream:
            got_value.append(value)
            if len(got_value) == 5:
                break

    async def push(stream):
        for i in range(5):
            await asyncio.sleep(0.1)
            stream.push(5)

    async def run():
        stream = gully.Gully()
        await asyncio.gather(push(stream), watch(stream))

    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())

    assert got_value == [5, 5, 5, 5, 5]


def test_stream_limit():
    got_value = []

    async def watch(stream):
        async for value in stream.limit(5):
            got_value.append(value)

    async def push(stream):
        for i in range(6):
            await asyncio.sleep(0.1)
            stream.push(5)

    async def run():
        stream = gully.Gully()
        await asyncio.gather(push(stream), watch(stream))

    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())

    assert got_value == [5, 5, 5, 5, 5]


def test_stream_filter():
    got_value = []

    async def watch(stream):
        async for value in stream.filter(lambda v: v % 2 == 0):
            got_value.append(value)

    async def push(stream):
        for i in range(6):
            await asyncio.sleep(0.1)
            stream.push(i)

        stream.stop()

    async def run():
        stream = gully.Gully()
        await asyncio.gather(push(stream), watch(stream))

    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())

    assert got_value == [0, 2, 4]


def test_stream_map():
    got_value = []

    async def watch(stream):
        async for value in stream.map(lambda v: v * 5):
            got_value.append(value)

    async def push(stream):
        for i in range(1000):
            await asyncio.sleep(0.001)
            stream.push(1)

        stream.stop()

    async def run():
        stream = gully.Gully()
        await asyncio.gather(push(stream), watch(stream))

    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())

    assert got_value == [5] * 1000
