from curio import sleep, spawn, run, CancelledError

async def sleeper(n):
    print('Sleeping for', n)
    await sleep(n)
    print('Awake again')

async def coro():
    task = await spawn(sleeper, 10)
    try:
        await task.join()
    except CancelledError:
        print('Cancelled')
        raise

async def main():
    task = await spawn(coro)
    await sleep(2)
    await task.cancel()
    print("here")

run(main)