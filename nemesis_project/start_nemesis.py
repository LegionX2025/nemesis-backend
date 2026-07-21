import os
import sys
import subprocess
import threading
import time

def print_header():
    print("==================================================================")
    print(" 🚀 NEMESIS OMNI-CONTROL CENTER ")
    print("==================================================================")
    print(" 1) Start Standard Local Dev Mode (Uvicorn + Vite)")
    print(" 2) Start Cloudflare Edge Simulator (Wrangler Backend + Frontend)")
    print(" 3) Auto-Deploy to Production Cloudflare (Runs auto_deploy.py)")
    print(" 4) Exit")
    print("==================================================================")

def stream_output(process, prefix):
    """Reads lines from the process stdout and prints them with a prefix."""
    for line in iter(process.stdout.readline, ''):
        if line:
            print(f"{prefix} {line.strip()}")
    process.stdout.close()

def run_concurrently(commands):
    """
    Runs multiple commands concurrently and streams their output with a prefix.
    commands is a list of tuples: (command_string, working_directory, prefix_string)
    """
    processes = []
    threads = []
    
    for cmd, cwd, prefix in commands:
        print(f"[*] Starting {prefix} -> {cmd} in {cwd}")
        # Need shell=True for npm/npx/uvicorn resolution on Windows
        p = subprocess.Popen(
            cmd, 
            shell=True, 
            cwd=cwd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True,
            bufsize=1
        )
        processes.append(p)
        
        t = threading.Thread(target=stream_output, args=(p, prefix))
        t.daemon = True
        t.start()
        threads.append(t)
        
    try:
        # Keep main thread alive while subprocesses run
        while True:
            time.sleep(1)
            # If all processes die, exit
            if all(p.poll() is not None for p in processes):
                break
    except KeyboardInterrupt:
        print("\n[!] Shutting down all processes...")
        for p in processes:
            p.terminate()
        sys.exit(0)

def start_local_dev():
    print("\n>>> Starting Standard Local Development Mode...")
    commands = [
        ("uvicorn main:app --host 0.0.0.0 --port 10000 --reload", ".", "[BACKEND]"),
        ("npm run dev", "frontend", "[FRONTEND]")
    ]
    run_concurrently(commands)

def start_cloudflare_simulator():
    print("\n>>> Starting Cloudflare Edge Simulator Mode...")
    print("[*] Building frontend for Cloudflare Pages simulation first...")
    
    # Must build frontend first for Pages Dev
    build_process = subprocess.run("npm run build", shell=True, cwd="frontend")
    if build_process.returncode != 0:
        print("[!] Frontend build failed. Cannot start Pages Dev.")
        return
        
    commands = [
        ("npx wrangler dev -c wrangler.toml", "nemesis_python_worker", "[CF-WORKER]"),
        ("npx wrangler pages dev dist", "frontend", "[CF-PAGES]")
    ]
    run_concurrently(commands)

def main():
    while True:
        print_header()
        choice = input("Select an option [1-4]: ").strip()
        
        if choice == '1':
            start_local_dev()
            break
        elif choice == '2':
            start_cloudflare_simulator()
            break
        elif choice == '3':
            if os.path.exists("auto_deploy.py"):
                subprocess.run("python auto_deploy.py", shell=True)
            else:
                print("[!] auto_deploy.py not found.")
            break
        elif choice == '4':
            print("Exiting...")
            sys.exit(0)
        else:
            print("[!] Invalid option. Please try again.\n")

if __name__ == "__main__":
    main()
