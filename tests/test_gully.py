import asyncio
import gully


NoOp = type("NoOp", tuple(), {"__await__": lambda self: (None for _ in range(1))})()


def test_watcher():
    found = []

    async def watch(item):
        found.append(item)

    async def test():
        g = gully.Gully()
        g.watch(watch)
        await g.push("testing")
        await g.push("foobar")

    asyncio.run(test())
    assert found == ["testing", "foobar"]


def test_watcher_massive_data():
    c = 0

    async def watch(item):
        nonlocal c
        c += 1

    async def test():
        g = gully.Gully()
        g.watch(watch)
        for i in range(100_000):
            await g.push(i)

    asyncio.run(test())
    assert c == 100_000


def test_lots_of_watchers():
    c = 0

    async def test():
        g = gully.Gully()
        for _ in range(100_000):

            async def watch(item):
                nonlocal c
                c += 1

            g.watch(watch)

        await g.push(1)

    asyncio.run(test())
    assert c == 100_000


def test_observer_stop():
    c = 0

    async def watch(item):
        nonlocal c
        c += 1

    async def test():
        g = gully.Gully()
        observer = g.watch(watch)
        await g.push(1)
        observer.disable()
        await g.push(2)

    asyncio.run(test())
    assert c == 1


def test_observer_restart():
    c = 0

    async def watch(item):
        nonlocal c
        c += 1

    async def test():
        g = gully.Gully()
        observer = g.watch(watch)
        await g.push(1)
        observer.disable()
        await g.push(2)
        observer.enable()
        await g.push(3)

    asyncio.run(test())
    assert c == 2


def test_sub_gully():
    c = 0

    async def watch(item):
        nonlocal c
        c += 1

    async def test():
        g1 = gully.Gully()
        g2 = gully.Gully(g1)
        g2.watch(watch)
        await g1.push(1)
        await NoOp

    asyncio.run(test())
    assert c == 1


def test_filters():
    async def test():
        g = gully.Gully()

        g.add_filter(lambda item: item % 2 == 0)

        for i in range(1, 4):
            await g.push(i)

        return g.history

    x = asyncio.run(test())
    assert x == [2]


def test_filters_multiple():
    async def test():
        g = gully.Gully()

        g.add_filter(lambda item: item % 3 == 0, lambda item: item % 5 == 0)

        for i in range(1, 16):
            await g.push(i)

        return g.history

    x = asyncio.run(test())
    assert x == [15]


def test_map():
    async def test():
        g = gully.Gully()

        g.add_mapping(lambda item: item % 2 == 0)

        for i in range(1, 4):
            await g.push(i)

        return g.history

    x = asyncio.run(test())
    assert x == [False, True, False]


def test_map_multiple():
    async def test():
        g = gully.Gully()

        g.add_mapping(
            lambda item: item % 2 == 0, lambda item: "Even" if item else "Odd"
        )

        for i in range(1, 4):
            await g.push(i)

        return g.history

    x = asyncio.run(test())
    assert x == ["Odd", "Even", "Odd"]


def test_map_and_filter():
    async def test():
        g1 = gully.Gully(filters=[lambda item: item % 3 == 0])
        g2 = g1.map(
            lambda item: item % 2 == 0,
            lambda item: "Even" if item else "Odd",
        )

        for i in range(1, 10):
            await g1.push(i)

        await NoOp

        return g1.history, g2.history

    x, y = asyncio.run(test())
    assert x == [9, 6, 3]
    assert y == ["Odd", "Even", "Odd"]
