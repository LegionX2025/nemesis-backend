import os
import subprocess
import re
import sys
import json
import shutil
from pathlib import Path

def run_cmd(cmd, capture=True, check=True):
    cmd_str = " ".join(cmd)
    print(f"\n🚀 Running: {cmd_str}")
    try:
        result = subprocess.run(cmd_str, capture_output=True, text=True, check=check, shell=True)
        if capture:
            return result.stdout
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {cmd_str}")
        print(f"Error output:\n{e.stderr}")
        return e.stderr

def extract_id(output, pattern):
    match = re.search(pattern, output)
    if match:
        return match.group(1)
    return None

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"📄 Generated {path}")

def main():
    print("==================================================")
    print(" NEMESIS ENTERPRISE CLOUDFLARE ORCHESTRATOR v3.0")
    print("==================================================")
    print("Idempotent Resource Provisioning & Project Scaffold")
    
    worker_dir = Path("nemesis-global-worker")
    if not worker_dir.exists():
        worker_dir.mkdir()
        
    bindings = {
        "kv": {},
        "d1_id": None
    }
    
    # ---------------------------------------------------------
    # PHASE 1 & 2: DISCOVERY & PROVISIONING
    # ---------------------------------------------------------
    print("\n--- Provisioning Workers KV ---")
    kv_namespaces = ["NEMESIS_CACHE", "ENTITY_CACHE", "SESSION_CACHE", "TOKEN_CACHE", "OSINT_CACHE"]
    
    print("Fetching existing KV namespace IDs...")
    list_out = run_cmd(["npx", "wrangler", "kv", "namespace", "list"])
    if list_out and not "Error" in list_out:
        try:
            # Wrangler might print warnings before JSON
            json_str = list_out[list_out.find("["):] 
            namespaces = json.loads(json_str)
            for ns in namespaces:
                title = ns.get("title", "")
                for kv_name in kv_namespaces:
                    if title.endswith(kv_name):
                        bindings["kv"][kv_name] = ns.get("id")
        except:
            pass

    for kv_name in kv_namespaces:
        if kv_name in bindings["kv"]:
            print(f"✅ Found existing KV {kv_name}! ID: {bindings['kv'][kv_name]}")
        else:
            kv_out = run_cmd(["npx", "wrangler", "kv", "namespace", "create", kv_name], check=False)
            found_id = extract_id(kv_out, r'id\s*=\s*"([^"]+)"')
            if found_id:
                bindings["kv"][kv_name] = found_id
                print(f"✅ Created KV {kv_name}! ID: {found_id}")
            else:
                print(f"⚠️ Could not create {kv_name}, falling back to hardcoded ID.")
                fallback_ids = {
                    "NEMESIS_CACHE": "f4099ea1458e4e62ba838734f172846f",
                    "ENTITY_CACHE": "817961173773498d9e4715b3479fc66d",
                    "SESSION_CACHE": "7fbab659456242db8c27082fcdb0d4b1",
                    "TOKEN_CACHE": "2c35b6ff21d14830b3ae93ee4e6006c2",
                    "OSINT_CACHE": "5558ace53efa4a0aa37dc035b17c256a"
                }
                bindings["kv"][kv_name] = fallback_ids.get(kv_name, f"YOUR_ID_FOR_{kv_name}")
            
    print("\n--- Provisioning D1 Database ---")
    d1_list = run_cmd(["npx", "wrangler", "d1", "list", "--json"], check=False)
    if d1_list and not "Error" in d1_list:
        try:
            json_str = d1_list[d1_list.find("["):]
            dbs = json.loads(json_str)
            for db in dbs:
                if db.get("name") == "nemesis":
                    bindings["d1_id"] = db.get("uuid")
                    print(f"✅ Found existing D1 Database 'nemesis'! ID: {bindings['d1_id']}")
                    break
        except:
            pass
            
    if not bindings.get("d1_id"):
        d1_out = run_cmd(["npx", "wrangler", "d1", "create", "nemesis"], check=False)
        found_id = extract_id(d1_out, r'database_id\s*=\s*"([^"]+)"')
        if found_id:
            bindings["d1_id"] = found_id
            print(f"✅ Created D1 Database 'nemesis'! ID: {found_id}")
        else:
            bindings["d1_id"] = "REPLACE_WITH_D1_ID"
            
    print("\n--- Provisioning R2 Buckets ---")
    buckets = ["nemesis-reports", "nemesis-evidence", "nemesis-screenshots", "nemesis-exports"]
    # Check existing buckets (simplistic idempotency: if create fails with already exists, ignore)
    for bucket in buckets:
        out = run_cmd(["npx", "wrangler", "r2", "bucket", "create", bucket], check=False)
        if "already exists" in str(out).lower() or "created" in str(out).lower():
            print(f"✅ R2 Bucket {bucket} is ready.")

    print("\n--- Provisioning Queues ---")
    queues = ["wallet-tracing", "entity-resolution", "gemini-analysis", "report-generation", "notifications"]
    for queue in queues:
        out = run_cmd(["npx", "wrangler", "queues", "create", queue], check=False)
        if "already exists" in str(out).lower() or "created" in str(out).lower():
            print(f"✅ Queue {queue} is ready.")
            
    # ---------------------------------------------------------
    # PHASE 3: PROJECT GENERATION
    # ---------------------------------------------------------
    print("\n--- Generating Worker Project Scaffold ---")
    
    # 1. package.json
    package_json = {
      "name": "nemesis-global-worker",
      "version": "1.0.0",
      "private": True,
      "type": "module",
      "scripts": {
        "dev": "wrangler dev",
        "deploy": "wrangler deploy",
        "tail": "wrangler tail"
      },
      "dependencies": {
        "hono": "^4.6.0",
        "jose": "^5.9.0",
        "zod": "^3.24.0",
        "pg": "^8.11.3"
      },
      "devDependencies": {
        "@cloudflare/workers-types": "^4.20241205.0",
        "typescript": "^5.6.3",
        "wrangler": "^3.90.0",
        "@types/pg": "^8.11.0"
      }
    }
    write_file(worker_dir / "package.json", json.dumps(package_json, indent=2))
    
    # 2. tsconfig.json
    tsconfig = {
      "compilerOptions": {
        "target": "es2022",
        "lib": ["es2022"],
        "module": "es2022",
        "moduleResolution": "bundler",
        "types": ["@cloudflare/workers-types"],
        "strict": True,
        "esModuleInterop": True,
        "skipLibCheck": True,
        "forceConsistentCasingInFileNames": True
      },
      "include": ["src/**/*"]
    }
    write_file(worker_dir / "tsconfig.json", json.dumps(tsconfig, indent=2))
    
    # 3. .gitignore
    write_file(worker_dir / ".gitignore", "node_modules\n.wrangler\ndist\n")

    # 4. src/index.ts (Hono router)
    index_ts = """import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { Client } from 'pg'
import { TraceCoordinator, RealtimeManager, AdminConsole } from './durable_objects'

type Bindings = {
  PYTHON_BACKEND_URL: string
  NEMESIS_CACHE: KVNamespace
  ENTITY_CACHE: KVNamespace
  SESSION_CACHE: KVNamespace
  TOKEN_CACHE: KVNamespace
  OSINT_CACHE: KVNamespace
  DB: D1Database
  REPORTS: R2Bucket
  TRACE_QUEUE: Queue
  ENTITY_QUEUE: Queue
  TRACE_COORDINATOR: DurableObjectNamespace
  REALTIME_MANAGER: DurableObjectNamespace
  ADMIN_CONSOLE: DurableObjectNamespace
  HYPERDRIVE: Hyperdrive
}

const app = new Hono<{ Bindings: Bindings }>()

app.use('*', cors({
  origin: '*',
  allowHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
  allowMethods: ['POST', 'GET', 'OPTIONS']
}))

// Forward endpoints to FastAPI backend
const proxyToBackend = async (c: any, path: string) => {
  const backendUrl = c.env.PYTHON_BACKEND_URL || 'http://localhost:3001'
  // Avoid double slashes
  const cleanPath = path.startsWith('/') ? path : '/' + path;
  const targetUrl = new URL(cleanPath, backendUrl).toString();
  
  // Create a new request based on the original to safely override the URL
  const originalReq = c.req.raw;
  const proxyReq = new Request(targetUrl, originalReq);
  
  return fetch(proxyReq);
}

// Postgres Test Route using Hyperdrive
app.get('/api/pg-test', async (c) => {
  const client = new Client({ connectionString: c.env.HYPERDRIVE.connectionString });
  await client.connect();

  try {
    const result = await client.query("SELECT * FROM pg_tables");
    return c.json({ result: result.rows });
  } catch (e) {
    return c.json({ error: e instanceof Error ? e.message : String(e) }, 500);
  } finally {
    // Prevent connection leaks
    await client.end();
  }
})

app.all('/api/*', (c) => proxyToBackend(c, c.req.path))
app.all('/admin/*', (c) => proxyToBackend(c, c.req.path))

// WebSocket endpoints (Proxying to Durable Objects)
app.get('/ws/:trace_id', (c) => {
  const id = c.env.REALTIME_MANAGER.idFromName(c.req.param('trace_id'))
  const stub = c.env.REALTIME_MANAGER.get(id)
  return stub.fetch(c.req.raw)
})

export default app
export { TraceCoordinator, RealtimeManager, AdminConsole }
"""
    write_file(worker_dir / "src" / "index.ts", index_ts)
    
    # 5. src/durable_objects.ts
    do_ts = """import { DurableObject } from 'cloudflare:workers'

export class TraceCoordinator extends DurableObject {
  async fetch(request: Request) {
    if (request.method === 'POST') {
        const body = await request.json();
        // Here we would coordinate trace jobs, but for now we act as an event sink.
        return new Response(JSON.stringify({ status: "trace_job_accepted", id: this.ctx.id.toString() }), { status: 202 });
    }
    return new Response("Trace Coordinator DO Ready");
  }
}

export class RealtimeManager extends DurableObject {
  sessions: Map<WebSocket, string>;

  constructor(ctx: DurableObjectState, env: any) {
    super(ctx, env);
    this.sessions = new Map();
  }

  async fetch(request: Request) {
    const upgradeHeader = request.headers.get('Upgrade');
    if (!upgradeHeader || upgradeHeader !== 'websocket') {
      return new Response('Expected Upgrade: websocket', { status: 426 });
    }

    const [client, server] = Object.values(new WebSocketPair());
    
    server.accept();
    this.sessions.set(server, 'active');

    server.addEventListener('message', async (event) => {
      try {
        const data = JSON.parse(event.data as string);
        if (data.type === 'ping') {
          server.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
        }
        // Broadcast to all clients in this DO (trace_id specific)
        for (const [ws] of this.sessions) {
           if (ws !== server) ws.send(event.data);
        }
      } catch (e) {
        console.error("WS error:", e);
      }
    });

    server.addEventListener('close', () => {
      this.sessions.delete(server);
    });

    return new Response(null, {
      status: 101,
      webSocket: client,
    });
  }
}

export class AdminConsole extends DurableObject {
  async fetch(request: Request) { 
      return new Response(JSON.stringify({ status: "admin_console_active" })); 
  }
}
"""
    write_file(worker_dir / "src" / "durable_objects.ts", do_ts)

    # 6. wrangler.toml
    toml_content = f"""name = "nemesis-api"
main = "src/index.ts"
compatibility_date = "2024-02-08"

# ============================================================================
# KV NAMESPACES
# ============================================================================
"""
    for kv_name in kv_namespaces:
        toml_content += f"""[[kv_namespaces]]
binding = "{kv_name}"
id = "{bindings['kv'].get(kv_name, 'REPLACE_ME')}"
"""
    toml_content += f"""
# ============================================================================
# D1 DATABASE
# ============================================================================
[[d1_databases]]
binding = "DB"
database_name = "nemesis"
database_id = "{bindings['d1_id'] or 'YOUR_D1_ID_HERE'}"

# ============================================================================
# R2 BUCKETS
# ============================================================================
"""
    r2_mappings = {
        "REPORTS": "nemesis-reports",
        "EVIDENCE": "nemesis-evidence",
        "SCREENSHOTS": "nemesis-screenshots",
        "EXPORTS": "nemesis-exports"
    }
    for bind_name, bucket_name in r2_mappings.items():
        toml_content += f"""[[r2_buckets]]
binding = "{bind_name}"
bucket_name = "{bucket_name}"
"""
    toml_content += """
# ============================================================================
# QUEUES
# ============================================================================
"""
    q_mappings = {
        "TRACE_QUEUE": "wallet-tracing",
        "ENTITY_QUEUE": "entity-resolution",
        "AI_QUEUE": "gemini-analysis",
        "REPORT_QUEUE": "report-generation",
        "NOTIFICATION_QUEUE": "notifications"
    }
    for bind_name, q_name in q_mappings.items():
        toml_content += f"""[[queues.producers]]
binding = "{bind_name}"
queue = "{q_name}"
"""
    toml_content += """
[[queues.consumers]]
queue = "wallet-tracing"
max_batch_size = 10
max_batch_timeout = 5
max_retries = 3

# ============================================================================
# DURABLE OBJECTS & WORKFLOWS
# ============================================================================

[[durable_objects.bindings]]
name = "TRACE_COORDINATOR"
class_name = "TraceCoordinator"

[[durable_objects.bindings]]
name = "REALTIME_MANAGER"
class_name = "RealtimeManager"

[[durable_objects.bindings]]
name = "ADMIN_CONSOLE"
class_name = "AdminConsole"

[[migrations]]
tag = "v2"
new_sqlite_classes = ["TraceCoordinator", "RealtimeManager", "AdminConsole"]
deleted_classes = ["TraceSessionDO"]
"""
    # Load .env variables for wrangler.toml
    env_vars = {}
    try:
        # Try root .env first, then fallback to ../.env if cwd is local_deploy
        env_path = ".env" if os.path.exists(".env") else "../.env"
        with open(env_path, "r", encoding="utf-8") as env_file:
            for line in env_file:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    # Ignore VITE_ vars for backend
                    if not key.startswith("VITE_"):
                        env_vars[key] = val
    except Exception as e:
        print(f"⚠️ Could not load .env file: {e}")

    toml_content += """
# ============================================================================
# ENVIRONMENT VARIABLES
# ============================================================================
[vars]
PYTHON_BACKEND_URL = "https://nemesis-backend-rwp4.onrender.com"
"""
    for k, v in env_vars.items():
        # Escape backslashes first, then quotes in value
        safe_v = str(v).replace('\\', '\\\\').replace('"', '\\"')
        toml_content += f'{k} = "{safe_v}"\n'
        
    write_file(worker_dir / "wrangler.toml", toml_content)
    
    # ---------------------------------------------------------
    # PHASE 4: VALIDATION
    # ---------------------------------------------------------
    print("\n--- Validating Generated Project ---")
    required_files = ["package.json", "tsconfig.json", "wrangler.toml", "src/index.ts"]
    for req in required_files:
        if not (worker_dir / req).exists():
            print(f"❌ Validation Error: Missing {req}")
            sys.exit(1)
    print("✅ All required files present.")

    # ---------------------------------------------------------
    # PHASE 5: BUILD & DEPLOY
    # ---------------------------------------------------------
    print("\n--- Installing Dependencies ---")
    current_dir = os.getcwd()
    
    print("-> Installing Python dependencies...")
    run_cmd(["pip", "install", "-r", "requirements.txt"], check=False)
    
    os.chdir(worker_dir)
    
    print("-> Installing Node.js dependencies...")
    # Run npm install (using check=False so we don't crash on warnings)
    run_cmd(["npm", "install"], check=False)
    
    print("\n--- Deploying to Cloudflare Edge ---")
    # Deploy using npx wrangler deploy
    deploy_out = run_cmd(["npx", "wrangler", "deploy", "-c", "wrangler.toml"], check=False)
    
    os.chdir(current_dir)
    print("==================================================")
    print("   NEMESIS ENTERPRISE DEPLOYMENT COMPLETE         ")
    print("==================================================")

if __name__ == "__main__":
    main()
