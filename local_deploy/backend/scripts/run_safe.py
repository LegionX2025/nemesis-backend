import os
import sys
import uvicorn
import socket

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def run_server():
    port = 8088
    # Try to bind to 8088 to see if it's available
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('', port))
        s.close()
        print("[+] Starting Main Engine Instance on port 8088...")
    except OSError:
        port = find_free_port()
        print(f"[!] Primary port 8088 taken. Starting Sub-Instance on port {port}...")
    
    backend_app_dir = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "app")
    os.environ["NEMESIS_PORT"] = str(port)
    uvicorn.run("main:app", host="0.0.0.0", port=port, workers=4, app_dir=backend_app_dir)

if __name__ == "__main__":
    run_server()
