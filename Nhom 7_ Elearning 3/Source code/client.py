import asyncio
import os

CHUNK_SIZE = 1024  # 1KB

async def send_file(filename):
    reader, writer = await asyncio.open_connection("127.0.0.1", 8888)

    filesize = os.path.getsize(filename)
    sent = 0

    print(f"📤 Bắt đầu gửi {filename} ({filesize} bytes)")

    # Gửi tên file + size
    writer.write(f"{filename}|{filesize}\n".encode())
    await writer.drain()

    with open(filename, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break

            writer.write(chunk)
            await writer.drain()

            sent += len(chunk)
            percent = sent * 100 / filesize
            print(f"➡️ {filename}: {percent:.1f}%")

            await asyncio.sleep(0.2)  # 👈 làm chậm để THẤY RÕ bất đồng bộ

    writer.close()
    await writer.wait_closed()

    print(f"✅ Gửi xong {filename}")

async def main():
    task1 = asyncio.create_task(send_file("file1.txt"))
    task2 = asyncio.create_task(send_file("file2.txt"))

    await asyncio.gather(task1, task2)

    print("🎉 Hoàn thành tất cả file")

asyncio.run(main())
