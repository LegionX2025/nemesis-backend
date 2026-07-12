import sys
import os
import uvicorn

# Add backend/app to path to resolve any absolute imports within the app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend", "app"))

if __name__ == "__main__":
    # Render automatically sets the PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    # Run the ASGI app from the backend module
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port, workers=1)
