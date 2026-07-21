import subprocess
import sys
import os
import time

def main():
    print("========================================")
    print("   NEMESIS FULL STACK LAUNCH SEQUENCE")
    print("========================================")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(base_dir, "frontend")
    boot_script = os.path.join(base_dir, "backend", "boot.py")

    # 1. Start the Frontend Server in the background
    print("[*] Launching Frontend Server on Port 3000...")
    frontend_process = subprocess.Popen(
        [sys.executable, "-m", "http.server", "3000", "--directory", "frontend"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    time.sleep(1) # Give the frontend a second to bind to port 3000
    
    # 2. Start the Backend Server
    print("[*] Launching Backend Server (Diagnostics & API)...")
    print("========================================\n")
    try:
        # Popen without DEVNULL will stream the backend output directly to your terminal
        backend_process = subprocess.Popen(
            [sys.executable, boot_script]
        )
        
        time.sleep(2)
        print("\n\033[92m=== SYSTEM IS ONLINE ===\033[0m")
        print("-> Frontend UI: http://localhost:3000/index.html")
        print("-> Backend API: http://localhost:8088")
        print("-> Press Ctrl+C anytime to stop both servers.")
        print("\nStreaming backend logs below:\n")
        
        # Block and wait for the backend process
        backend_process.wait()
        
    except KeyboardInterrupt:
        print("\n[*] Shutting down servers...")
    finally:
        # Ensure the frontend server is killed when we exit
        frontend_process.terminate()
        try:
            backend_process.terminate()
        except Exception:
            pass
        print("[OK] All systems offline.")

if __name__ == "__main__":
    # Enable terminal colors
    os.system('color')
    main()
