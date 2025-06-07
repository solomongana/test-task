import asyncio
import os
from nio import AsyncClient, MatrixRoom, RoomMessageText


async def main():
    homeserver = os.environ.get("MATRIX_HOMESERVER")
    user = os.environ.get("MATRIX_USER")
    password = os.environ.get("MATRIX_PASSWORD")
    room_id = os.environ.get("MATRIX_ROOM")
    if not all([homeserver, user, password, room_id]):
        raise SystemExit("Missing Matrix configuration environment variables")

    client = AsyncClient(homeserver, user)
    await client.login(password)
    await client.join(room_id)

    async def message_cb(room: MatrixRoom, event: RoomMessageText) -> None:
        if event.sender != client.user:
            await client.room_send(
                room.room_id,
                message_type="m.room.message",
                content={"msgtype": "m.text", "body": event.body},
            )

    client.add_event_callback(message_cb, RoomMessageText)

    await client.sync_forever(timeout=30000)


if __name__ == "__main__":
    asyncio.run(main())
