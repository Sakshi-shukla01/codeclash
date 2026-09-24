"""
Real-time events: server se user ke browser tak messages bhejna.

Kyun Redis Pub/Sub? Agar backend ke 3 copies (servers) chal rahe hain, toh ho sakta hai
Rahul server-1 se connected ho aur Priya server-2 se. Event Redis pe publish hota hai,
aur jis server pe bhi user connected hai, woh message utha ke WebSocket pe bhej deta hai.
Isse WebSockets horizontally scale ho jaate hain.
"""
import asyncio
import json
import logging

from fastapi import WebSocket

from app.db.redis import Keys, redis_client

log = logging.getLogger("codeclash.events")


async def notify(user_id: int, event: dict) -> None:
    await redis_client.publish(Keys.user_events(user_id), json.dumps(event))


class ConnectionManager:
    """Is server process pe kaunsa user kaunse WebSocket(s) se connected hai."""

    def __init__(self):
        self.connections: dict[int, set[WebSocket]] = {}

    def add(self, user_id: int, ws: WebSocket):
        self.connections.setdefault(user_id, set()).add(ws)

    def remove(self, user_id: int, ws: WebSocket):
        conns = self.connections.get(user_id)
        if conns:
            conns.discard(ws)
            if not conns:
                del self.connections[user_id]

    def is_online(self, user_id: int) -> bool:
        return user_id in self.connections

    async def send_local(self, user_id: int, message: str):
        for ws in list(self.connections.get(user_id, ())):
            try:
                await ws.send_text(message)
            except Exception:
                self.remove(user_id, ws)


manager = ConnectionManager()


async def pubsub_listener():
    """Background task: Redis ke 'events:user:*' channels sunta hai aur local WebSockets pe bhejta hai."""
    while True:
        try:
            pubsub = redis_client.pubsub()
            await pubsub.psubscribe("events:user:*")
            async for msg in pubsub.listen():
                if msg["type"] != "pmessage":
                    continue
                user_id = int(msg["channel"].rsplit(":", 1)[1])
                if manager.is_online(user_id):
                    await manager.send_local(user_id, msg["data"])
        except asyncio.CancelledError:
            raise
        except Exception as e:
            log.warning("pubsub listener error: %s, reconnecting...", e)
            await asyncio.sleep(1)
