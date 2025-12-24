import asyncio
import os

SAVE_DIR = "received"
os.makedirs(SAVE_DIR, exist_ok=True)

async def handle_client(reader, writer):
    header = await reader.readline()
    filename, filesize = header.decode().strip().split("|")
    filesize = int(filesize)

    print(f"📥 Nhận {filename} ({filesize} bytes)")

    received = 0
    path = os.path.join(SAVE_DIR, filename)

    with open(path, "wb") as f:
        while received < filesize:
            data = await reader.read(1024)
            if not data:
                break
            f.write(data)
            received += len(data)

    print(f"✅ Nhận xong {filename}")
    writer.close()

async def main():
    server = await asyncio.start_server(handle_client, "0.0.0.0", 8888)
    print("🟢 Server đang chạy cổng 8888")
    async with server:
        await server.serve_forever()

asyncio.run(main())
