import asyncio
import pipes


def test_pipe_on_next():
    got_value = None

    def watch(value):
        nonlocal got_value
        got_value = value

    async def push(pipe):
        pipe.push(5)

    async def run():
        pipe = pipes.Pipe()
        pipe.on_next(watch)
        await asyncio.sleep(0.1)
        await push(pipe)

    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())

    assert got_value == 5


def test_pipe_next():
    got_value = None

    async def watch(pipe):
        nonlocal got_value
        got_value = await pipe.next

    async def push(pipe):
        pipe.push(5)

    async def run():
        pipe = pipes.Pipe()
        loop.create_task(watch(pipe))
        await asyncio.sleep(0.1)
        await push(pipe)

    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())

    assert got_value == 5


def test_pipe_iterate():
    got_value = []

    async def watch(pipe):
        for value in pipe:
            got_value.append(value)

    async def push(pipe):
        pipe.push(1)
        pipe.push(2)
        pipe.push(3)
        pipe.push(4)
        await asyncio.sleep(0.1)
        pipe.push(5)
        pipe.close()

    async def run():
        pipe = pipes.Pipe()
        await asyncio.gather(push(pipe), watch(pipe))

    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())

    assert got_value == [1, 2, 3, 4]


def test_pipe_async_iterate():
    got_value = []

    async def watch(pipe):
        try:
            async for value in pipe:
                got_value.append(value)
        except asyncio.exceptions.CancelledError:
            ...

    async def push(pipe):
        pipe.push(1)
        pipe.push(2)
        pipe.push(3)
        pipe.push(4)
        await asyncio.sleep(0.1)
        pipe.push(5)
        pipe.close()

    async def run():
        pipe = pipes.Pipe()
        await asyncio.gather(push(pipe), watch(pipe))
        return pipe

    loop = asyncio.new_event_loop()
    p = loop.run_until_complete(run())

    assert got_value == [1, 2, 3, 4, 5]


def test_pipe_iterate_limit():
    got_value = []

    async def watch(pipe):
        for value in pipe.iterate_first(3):
            got_value.append(value)

    async def push(pipe):
        pipe.push(1)
        pipe.push(2)
        pipe.push(3)
        pipe.push(4)
        await asyncio.sleep(0.1)
        pipe.push(5)
        pipe.close()

    async def run():
        pipe = pipes.Pipe()
        await asyncio.gather(push(pipe), watch(pipe))

    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())

    assert got_value == [1, 2, 3]


def test_pipe_async_iterate_limit():
    got_value = []

    async def watch(pipe):
        try:
            async for value in pipe.iterate_first(3):
                got_value.append(value)
        except asyncio.exceptions.CancelledError:
            ...

    async def push(pipe):
        pipe.push(1)
        pipe.push(2)
        pipe.push(3)
        pipe.push(4)
        await asyncio.sleep(0.1)
        pipe.push(5)
        pipe.close()

    async def run():
        pipe = pipes.Pipe()
        await asyncio.gather(push(pipe), watch(pipe))
        return pipe

    loop = asyncio.new_event_loop()
    p = loop.run_until_complete(run())

    assert got_value == [1, 2, 3]
