"""
WebSocket endpoint:  ws://localhost:8000/ws?token=<JWT>

Har logged-in user ka ek WebSocket connection hota hai. Server is pe yeh events bhejta hai:
  match_found, submission_result, opponent_progress, opponent_typing, battle_end

Client yeh bhej sakta hai:
  {"type": "ping"}                          -> {"type": "pong"}
  {"type": "typing", "match_id": 42}        -> opponent ko "typing..." dikhta hai
"""
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import decode_access_token
from app.services.battle_manager import notify_typing
from app.services.events import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: str = ""):
    user_id = decode_access_token(token)
    if not user_id:
        await ws.close(code=4401)  # custom code: unauthorized
        return

    await ws.accept()
    manager.add(user_id, ws)
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if msg.get("type") == "ping":
                await ws.send_text(json.dumps({"type": "pong"}))
            elif msg.get("type") == "typing" and isinstance(msg.get("match_id"), int):
                await notify_typing(msg["match_id"], user_id)
    except WebSocketDisconnect:
        pass
    finally:
        manager.remove(user_id, ws)
