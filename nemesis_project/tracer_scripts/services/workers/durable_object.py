"""
NEMESIS v3.1 Enterprise
Cloudflare Durable Object: Session Engine
Handles WebSocket Hibernation, Analyst Collaboration, and Graph State persistence.
"""

import json
import logging
from typing import Dict, Any

logger = logging.getLogger("NEMESIS.DurableObjects.SessionEngine")

class SessionEngineDO:
    """
    Cloudflare Durable Object
    Terminates WebSockets at the Edge, bypassing the need for Socket.io or a Redis pub/sub broker.
    """
    
    def __init__(self, state, env):
        self.state = state
        self.env = env
        self.sessions: Dict[str, Any] = {}
        
    async def fetch(self, request):
        """HTTP Handler for internal DO interactions and WebSocket upgrades."""
        # 1. Internal Push Webhook (From Queue Consumers)
        if request.url.endswith("/push") and request.method == "POST":
            payload = await request.json()
            action = payload.get("action")
            if action == "broadcast":
                await self._broadcast_to_session(payload.get("session_id"), payload.get("payload"))
            return {"status": 200, "message": "Broadcast successful"}

        # 2. WebSocket Upgrade
        if request.headers.get("Upgrade") != "websocket":
            return {"status": 426, "message": "Expected WebSocket Upgrade"}
            
        # Accept the WebSocket connection natively on the Edge
        pair = await self.env.WebSocketPair()
        client_ws = pair[0]
        server_ws = pair[1]
        
        self.state.acceptWebSocket(server_ws)
        return {"status": 101, "webSocket": client_ws}
        
    async def webSocketMessage(self, ws, message):
        """Triggered upon receiving a message from a connected client."""
        try:
            data = json.loads(message)
            action = data.get("action")
            
            if action == "subscribe_graph":
                session_id = data.get("session_id")
                ws.serializeAttachment({"session_id": session_id})
                await self._broadcast_to_session(session_id, {"type": "system", "msg": "Analyst joined session."})
                
            elif action == "ai_query":
                # Push the heavy AI task into the Cloudflare Queue!
                await self.env.JOB_QUEUE.send({
                    "type": "ai_query",
                    "session_id": ws.deserializeAttachment().get("session_id"),
                    "prompt": data.get("prompt")
                })
                ws.send(json.dumps({"type": "ack", "msg": "AI Query queued for background processing."}))
                
        except Exception as e:
            logger.error(f"WS DO Error: {str(e)}")

    async def webSocketClose(self, ws, code, reason, wasClean):
        attachment = ws.deserializeAttachment()
        if attachment and "session_id" in attachment:
            await self._broadcast_to_session(attachment["session_id"], {"type": "system", "msg": "Analyst left session."})

    async def _broadcast_to_session(self, session_id: str, payload: dict):
        """Iterates through all hibernated WebSockets and broadcasts if they belong to the session."""
        sockets = self.state.getWebSockets()
        for s in sockets:
            attach = s.deserializeAttachment()
            if attach and attach.get("session_id") == session_id:
                s.send(json.dumps(payload))
