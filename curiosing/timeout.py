from curio import sleep, timeout_after, TaskTimeout, run

async def coro1():
  print('Coro1 Start')
  await sleep(10)
  print('Coro1 Success')


async def coro2():
  print('Coro2 Start')
  await sleep(1)
  print('Coro2 Success')


async def child():
  try:
    await timeout_after(50, coro1)
  except TaskTimeout:
    print('Coro1 Timeout')

  await coro2()


async def main():
  try:
    await timeout_after(5, child)
  except TaskTimeout:
    print('Parent Timeout')

run(main)
