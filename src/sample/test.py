import asyncio
from rahatline_py import RahatLine

ROOM_ID = '1'
JWT_SECRET = 'Key-Must-Be-at-least-32-bytes-in-length!'

async def main():
    conn = RahatLine.Initialize('localhost', 8080, ROOM_ID, JWT_SECRET)
    id = await conn.Connect()
    print(id)

asyncio.run(main())