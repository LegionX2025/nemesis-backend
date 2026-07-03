import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    print(f"🔧 Running: {cmd}")
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        text=True
    )
    
    output = []
    while True:
        stdout_line = process.stdout.readline()
        if stdout_line:
            print(f"  {stdout_line.strip()}")
            output.append(stdout_line)
        stderr_line = process.stderr.readline()
        if stderr_line:
            print(f"  [stderr] {stderr_line.strip()}")
            output.append(stderr_line)
            
        if stdout_line == '' and stderr_line == '' and process.poll() is not None:
            break
            
    return process.returncode, "".join(output)

if __name__ == "__main__":
    worker_dir = Path("nemesis-global-worker").resolve()
    print("🚀 Auto-Deploying Edge Worker")
    
    ret, out = run_command("npx wrangler deploy", cwd=worker_dir)
    if ret != 0:
        print("❌ Worker deployment failed!")
        
        # Auto-fix 1: Migration Error
        if "10097" in out:
            print("⚠️ Detected Migration Error 10097. Attempting auto-fix...")
            toml_path = worker_dir / "wrangler.toml"
            with open(toml_path, "r", encoding="utf-8") as f:
                c = f.read()
            c = c.replace('new_classes = ["TraceCoordinator"', 'new_sqlite_classes = ["TraceCoordinator"')
            with open(toml_path, "w", encoding="utf-8") as f:
                f.write(c)
            print("✅ Applied auto-fix for sqlite classes. Redeploying...")
            ret, out = run_command("npx wrangler deploy", cwd=worker_dir)
            
        if ret != 0:
            print("❌ Worker redeployment still failed. Please check logs.")
            sys.exit(1)
            
    print("✅ Worker deployed successfully!")
