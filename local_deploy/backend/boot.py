import sys
import os
import subprocess
import time
import urllib.request
import urllib.error
import json
import socket

def print_header(msg):
    print(f"\n{'='*50}\n=== {msg} ===\n{'='*50}")

def print_status(msg, status="OK", is_critical=False):
    color = "\033[92m" if status == "OK" else ("\033[93m" if not is_critical else "\033[91m")
    reset = "\033[0m"
    print(f"[*] {msg.ljust(40)} [{color}{status}{reset}]")

def run_cmd(cmd, desc):
    print(f"[*] {desc}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[!] Error during {desc}:\n{result.stderr}")
        return False
    return True

def step_1_install_dependencies():
    print_header("[1/6] Auto-Installing Dependencies")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    req_file = os.path.join(base_dir, "requirements.txt")
    if os.path.exists(req_file):
        print("[*] Verifying/Installing Python dependencies from requirements.txt...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file, "--quiet"])
        
        # Ensure playwright browsers are installed
        print("[*] Verifying/Installing Playwright Chromium browser...")
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
        print_status("Dependency Check", "OK")
    else:
        print_status("requirements.txt missing", "WARN", is_critical=False)

def check_tcp_port(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    try:
        s.connect((host, port))
        s.close()
        return True
    except:
        return False

def check_redis(redis_url):
    try:
        from redis import Redis
        # Simple redis check
        r = Redis.from_url(redis_url, socket_connect_timeout=2)
        r.ping()
        return True
    except Exception:
        return False

def check_postgres(pg_uri):
    try:
        import psycopg2
        conn = psycopg2.connect(pg_uri, connect_timeout=3)
        conn.close()
        return True
    except Exception:
        return False

def check_mongo(mongo_uri):
    try:
        from pymongo import MongoClient
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        return True
    except Exception:
        return False

def step_2_network_health():
    print_header("[2/6] Network & Core Health Check")
    try:
        urllib.request.urlopen("https://cloudflare.com", timeout=3)
        print_status("Outbound Internet", "OK")
    except Exception:
        print_status("Outbound Internet", "FAIL", is_critical=True)
    
    # Check if 8088 is already bound
    if check_tcp_port("127.0.0.1", 8088):
        print_status("Port 8088 Available", "IN USE", is_critical=False)
    else:
        print_status("Port 8088 Available", "OK")

def step_3_databases():
    print_header("[3/6] Database Connectivity Check")
    # Load env vars safely
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        load_dotenv(env_path)
    except ImportError:
        pass

    # Redis
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    if check_redis(redis_url):
        print_status("Redis Tracing Cache", "OK")
    else:
        print_status("Redis Tracing Cache", "DOWN (Warn)")

    # MongoDB
    mongo_uri = os.getenv("MONGODB_URI", os.getenv("DATABASE_MONGO_URL"))
    if mongo_uri and check_mongo(mongo_uri):
        print_status("MongoDB Connection", "OK")
    else:
        print_status("MongoDB Connection", "FAIL (Warn)")

    # Postgres
    pg_uri = os.getenv("POSTGRES_URI")
    if pg_uri and check_postgres(pg_uri):
        print_status("PostgreSQL Connection", "OK")
    else:
        print_status("PostgreSQL Connection", "FAIL (Warn)")

def check_jsonrpc(url):
    req = urllib.request.Request(url, method="POST")
    req.add_header('Content-Type', 'application/json')
    data = json.dumps({"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}).encode('utf-8')
    try:
        resp = urllib.request.urlopen(req, data=data, timeout=3)
        if resp.getcode() == 200:
            return True
    except Exception:
        pass
    return False

def step_4_api_chains():
    print_header("[4/6] API Provider & Chain Verification")
    gemini = os.getenv("GEMINI_API_KEYS", os.getenv("GEMINI_API_KEY"))
    if gemini and "AQ." in gemini:
        print_status("Gemini AI Provider", "OK")
    else:
        print_status("Gemini AI Provider", "MISSING (Critical)")

    infura = os.getenv("INFURA_ETHEREUM_MAINNET")
    if infura and check_jsonrpc(infura):
        print_status("Ethereum RPC Node", "OK")
    else:
        print_status("Ethereum RPC Node", "FAIL (Warn)")

def step_5_tracing_engine():
    print_header("[5/6] Tracing Engine Status")
    # Check if a Celery worker is alive
    print("[*] Checking Celery background workers...")
    try:
        # Pinging celery requires celery app, simple check using CLI
        result = subprocess.run([sys.executable, "-m", "celery", "-A", "app.celery_worker", "status"], capture_output=True, text=True, timeout=5, cwd=os.path.dirname(os.path.abspath(__file__)))
        if "OK" in result.stdout:
            print_status("Celery Workers", "OK")
        else:
            print_status("Celery Workers", "OFFLINE (Warn)")
    except Exception:
        print_status("Celery Workers", "OFFLINE (Warn)")

def step_6_launch():
    print_header("[6/6] Launching Nemesis Backend")
    app_dir = os.path.dirname(os.path.abspath(__file__))
    print("[*] Starting Uvicorn Server on http://127.0.0.1:8088...")
    os.chdir(app_dir)
    try:
        # Replace the current process with uvicorn
        import uvicorn
        # We import from app.main here to ensure all dependencies are loaded correctly
        from app.main import sio_app
        uvicorn.run(sio_app, host="127.0.0.1", port=8088, reload=False)
    except KeyboardInterrupt:
        print("\n[*] Server stopped by user.")
    except Exception as e:
        print(f"\n[!] Failed to start backend: {e}")

if __name__ == "__main__":
    # Ensure terminal colors work on windows
    os.system('color')
    step_1_install_dependencies()
    step_2_network_health()
    step_3_databases()
    step_4_api_chains()
    step_5_tracing_engine()
    step_6_launch()
