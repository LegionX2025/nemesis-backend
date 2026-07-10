import subprocess
import sys
import os

def install_requirements():
    print("==================================================")
    print("   [BOOT] AUTO-RESOLVING DEPENDENCIES             ")
    print("==================================================")
    try:
        # We enforce --no-cache-dir to bypass the Windows permission lock on 'stem' or any other package
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--no-cache-dir"],
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        print("\n[BOOT] All dependencies resolved successfully.\n")
    except subprocess.CalledProcessError as e:
        print(f"\n[BOOT] CRITICAL FAILURE: Could not install dependencies. Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # 1. Auto-check and install
    install_requirements()
    
    # 2. Continue to main application
    print("[BOOT] Handing over execution to main.py...\n")
    os.execv(sys.executable, [sys.executable, "main.py"])
