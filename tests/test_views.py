import asyncio
import gully


def test_stream_filter_view():
    got_value = []

    async def watch(stream):
        async for value in stream:
            got_value.append(value)

    async def push(stream):
        for i in range(5):
            stream.push(i)
            await asyncio.sleep(0.1)

    async def run():
        def f(p, value):
            return value % 2 == 0

        stream = gully.DataStream()
        view = stream.filter(f)
        loop.create_task(watch(view))
        await asyncio.sleep(0.1)
        await push(stream)
        view.close()

    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())

    assert got_value == [0, 2, 4]


def test_stream_map_view():
    got_value = []

    async def watch(stream):
        async for value in stream:
            got_value.append(value)

    async def push(stream):
        for i in range(5):
            stream.push(i)
            await asyncio.sleep(0.1)

    async def run():
        def m(p, value):
            return value * 2

        stream = gully.DataStream()
        view = stream.map(m)
        loop.create_task(watch(view))
        await asyncio.sleep(0.1)
        await push(stream)
        view.close()

    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())

    assert got_value == [0, 2, 4, 6, 8]


def test_stream_map_filter_view():
    got_value = []

    async def watch(stream):
        async for value in stream:
            got_value.append(value)

    async def push(stream):
        for i in range(5):
            stream.push(i)
            await asyncio.sleep(0.1)

    async def run():
        def f(p, value):
            return value % 2 == 0

        def m(p, value):
            return value * 2

        stream = gully.DataStream()
        view = stream.filter(f).map(m)
        loop.create_task(watch(view))
        await asyncio.sleep(0.1)
        await push(stream)
        view.close()

    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())

    assert got_value == [0, 4, 8]
