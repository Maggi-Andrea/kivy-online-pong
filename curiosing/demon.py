from curio import sleep, spawn, run

async def spinner():
  while True:
    print('Spinning')
    await sleep(5)


async def main():
  await spawn(spinner, daemon=True)
  await sleep(20)
  print('Main. Goodbye')


run(main)  # Runs until main() returns
print('Other. Goodbye')