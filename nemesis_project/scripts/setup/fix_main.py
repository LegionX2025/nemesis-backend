missing_code = """
@app.middleware('http')
async def validate_edge_signature(request, call_next):
    if request.url.path.startswith('/api/'):
        if request.method == 'OPTIONS': return await call_next(request)
    return await call_next(request)

import os
if os.path.exists('static'):
    app.mount('/static', StaticFiles(directory='static'), name='static')
elif os.path.exists('/session/metadata/static'):
    app.mount('/static', StaticFiles(directory='/session/metadata/static'), name='static')

active_sessions = {}
templates = Jinja2Templates(directory='templates')

@app.websocket('/api/godmode/stream')
async def godmode_ws_stream(websocket):
    await godmode_engine.connect(websocket)
    try:
        while True: data = await websocket.receive_text()
    except Exception: pass
    finally: godmode_engine.disconnect(websocket)

class GodmodeToggle(BaseModel):
    enabled: bool
"""
with open('main.py', 'r') as f:
    c = f.read()
c = c.replace('@app.post("/api/godmode/toggle")', missing_code + '\n@app.post("/api/godmode/toggle")')
with open('main.py', 'w') as f:
    f.write(c)
print('Fixed')
