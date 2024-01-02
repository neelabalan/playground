import asyncio


async def fibonacci(n):
    a, b = 0, 1
    for i in range(n):
        await asyncio.sleep(0)
        a, b = b, a + b
    return a


async def take_long_time():
    try:
        print('starting a function which will take long time...')
        response = await fibonacci(1000000)
        print('done!')
    except KeyboardInterrupt:
        print('exiting...')


async def test():
    try:
        await asyncio.sleep(1)
        print('test print')
    except KeyboardInterrupt:
        print('exiting...')


async def main():
    await asyncio.gather(take_long_time(), test())


if __name__ == '__main__':
    # s = time.perf_counter()
    asyncio.run(main())
    # elapsed = time.perf_counter() - s
    # print(f'{__file__} executed in {elapsed:0.2f} seconds')
