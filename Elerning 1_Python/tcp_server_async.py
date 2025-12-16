import asyncio

HOST = "0.0.0.0"
PORT = 8888

async def handle_client(reader, writer):
    addr = writer.get_extra_info("peername")
    print(f"[SERVER] Client connected: {addr}")

    while True:
        data = await reader.read(1024)
        if not data:
            print(f"[SERVER] Client disconnected: {addr}")
            break

        message = data.decode().strip()
        print(f"[SERVER] Received from client: {message}")

        # Xử lý đơn giản
        response = f"Server received: {message}"
        writer.write(response.encode())
        await writer.drain()

    writer.close()
    await writer.wait_closed()

async def main():
    server = await asyncio.start_server(
        handle_client, HOST, PORT
    )
    print(f"[SERVER] Async TCP server running on {HOST}:{PORT}")

    async with server:
        await server.serve_forever()

asyncio.run(main())
