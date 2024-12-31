import asyncio


async def f():
    pass


async def test_task_context():
    hmm = "hmm"

    task = asyncio.create_task(f())

    print(list(task.get_context().values()))

    assert task.get_context().get("hmm") == "hmm"

    await task

    print(hmm)
