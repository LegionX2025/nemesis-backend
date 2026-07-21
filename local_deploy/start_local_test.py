import os
import subprocess
import sys
import time

def start_servers():
    print("🚀 Starting Local Test Environment for NEMESIS...")
    
    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, "backend")
    frontend_dir = os.path.join(base_dir, "frontend")
    
    # 1. Start Backend
    print("-> Starting Uvicorn Backend API on port 8088...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8088"],
        cwd=os.path.join(backend_dir, "app"),
        env=os.environ.copy()
    )
    
    # Wait a moment for backend to initialize
    time.sleep(3)
    
    # 2. Start Frontend
    print("-> Starting Python HTTP Server for Frontend on port 8000...")
    frontend_process = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8000"],
        cwd=frontend_dir
    )
    
    print("\n" + "="*60)
    print("✅ ENVIRONMENT READY!")
    print("1. Backend API running at: http://127.0.0.1:8088")
    print("2. Frontend UI running at: http://127.0.0.1:8000/nemesis_id_new.html")
    print("\nYou can now open the frontend link in your browser and test the cases:")
    print("BTC: bc1qpa8n0a5ckt7wkdw3cn8eklsz3z0kn89knme5a9")
    print("XRP: ra58paZqDhh2e6LtA4VPQEgAztUz3Z3urq")
    print("ETH: 0x159a861a3f0838adb1e6895886c7a0be7158be89")
    print("SOL: uThZSCB2R8UQXHuPKPQLrRC5n7VTdSqUrJDQuoJsNum")
    print("="*60 + "\n")
    print("Press Ctrl+C to stop both servers.")
    
    try:
        backend_process.wait()
    except KeyboardInterrupt:
        print("\nStopping servers...")
        backend_process.terminate()
        frontend_process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    start_servers()
