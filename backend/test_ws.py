import asyncio
import websockets


async def test():
    uri = "ws://127.0.0.1:8000/ws/1?token="

    async with websockets.connect(uri) as ws:
        await ws.send('{"content": "hello"}')

        response = await ws.recv()
        print(response)


asyncio.run(test())