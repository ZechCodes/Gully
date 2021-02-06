import asyncio
import pipes


def test_pipe_filter_view():
    got_value = []

    async def watch(pipe):
        async for value in pipe:
            got_value.append(value)

    async def push(pipe):
        for i in range(5):
            pipe.push(i)
            await asyncio.sleep(0.1)

    async def run():
        def f(p, value):
            return value % 2 == 0

        pipe = pipes.Pipe()
        view = pipe.filter(f)
        loop.create_task(watch(view))
        await asyncio.sleep(0.1)
        await push(pipe)
        view.close()

    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())

    assert got_value == [0, 2, 4]


def test_pipe_map_view():
    got_value = []

    async def watch(pipe):
        async for value in pipe:
            got_value.append(value)

    async def push(pipe):
        for i in range(5):
            pipe.push(i)
            await asyncio.sleep(0.1)

    async def run():
        def m(p, value):
            return value * 2

        pipe = pipes.Pipe()
        view = pipe.map(m)
        loop.create_task(watch(view))
        await asyncio.sleep(0.1)
        await push(pipe)
        view.close()

    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())

    assert got_value == [0, 2, 4, 6, 8]


def test_pipe_map_filter_view():
    got_value = []

    async def watch(pipe):
        async for value in pipe:
            got_value.append(value)

    async def push(pipe):
        for i in range(5):
            pipe.push(i)
            await asyncio.sleep(0.1)

    async def run():
        def f(p, value):
            return value % 2 == 0

        def m(p, value):
            return value * 2

        pipe = pipes.Pipe()
        view = pipe.filter(f).map(m)
        loop.create_task(watch(view))
        await asyncio.sleep(0.1)
        await push(pipe)
        view.close()

    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())

    assert got_value == [0, 4, 8]
