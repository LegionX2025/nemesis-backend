import re
import os

app_path = r"c:\Users\LEGIONX\Downloads\cases\local_deploy\backend\app\main.py"

with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

# Check if root route exists
if '@app.get("/")' not in content:
    root_route = """
@app.get("/")
async def serve_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
"""
    # Inject it before @app.get("/api/v1/assets/resolve")
    content = content.replace('@app.get("/api/v1/assets/resolve")', root_route + '\n@app.get("/api/v1/assets/resolve")')
    
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: Added root route (/) pointing to index.html")
else:
    print("Root route already exists.")
