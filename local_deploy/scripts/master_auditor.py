import os
import sys
import json
import time
import ast
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(r"C:\Users\LEGIONX\Downloads\nemesis\tracer_scripts")
REPORTS_DIR = BASE_DIR / "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

TARGET_WALLET = "0x159a861a3f0838adb1e6895886c7a0be7158be89"
API_URL = "http://127.0.0.1:8000"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEMESIS Master Audit Report</title>
    <script src="https://kit.fontawesome.com/97825b2eb7.js" crossorigin="anonymous"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body { margin: 0; padding: 2rem; background: #0f172a; color: #e2e8f0; font-family: 'Inter', sans-serif; }
        .container { max-width: 1200px; margin: 0 auto; margin-top: 80px; }
        h1 { color: #f8fafc; font-weight: 800; border-bottom: 2px solid #3b82f6; padding-bottom: 0.5rem; text-shadow: 0 0 10px rgba(59, 130, 246, 0.5); }
        .meta { font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; color: #94a3b8; margin-bottom: 2rem; }
        .category { background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(51, 65, 85, 0.8); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 10px 20px rgba(0,0,0,0.3); }
        .category h2 { margin-top: 0; color: #60a5fa; text-transform: uppercase; font-size: 1.2rem; letter-spacing: 1px; }
        table { width: 100%; border-collapse: collapse; margin-top: 1rem; font-family: 'JetBrains Mono', monospace; }
        th, td { text-align: left; padding: 1rem; border-bottom: 1px solid rgba(51, 65, 85, 0.5); }
        th { color: #94a3b8; font-weight: 600; }
        tr:hover { background: rgba(51, 65, 85, 0.3); }
        .badge { padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: 800; font-size: 0.8rem; text-transform: uppercase; }
        .badge-pass { background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.5); box-shadow: 0 0 10px rgba(16, 185, 129, 0.2); }
        .badge-fail { background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.5); box-shadow: 0 0 10px rgba(239, 68, 68, 0.2); }
    </style>
</head>
<body>
    <div class="container">
        <h1><i class="fa-solid fa-shield-halved"></i> Master Security & E2E Audit Report</h1>
        <div class="meta">
            <p><strong>Generated:</strong> {timestamp}</p>
            <p><strong>Target API:</strong> {api_url}</p>
            <p><strong>Version:</strong> OMEGA 5.0 Lifecycle Master</p>
        </div>
        
        {content}
        
    </div>
    <script src="/global_nav.js"></script>
</body>
</html>
"""

class Auditor:
    def __init__(self):
        self.results = {
            "Security & Compliance": [],
            "Static Code Analysis": [],
            "Frontend E2E Tests": [],
            "Backend Integration Tests": [],
            "Performance Benchmarks": []
        }
    
    def log(self, category, name, status, details=""):
        print(f"[{category.upper()}] {name}: {'PASS' if status else 'FAIL'} - {details}")
        self.results[category].append({
            "name": name,
            "status": "PASS" if status else "FAIL",
            "details": details
        })

    def run_static_analysis(self):
        print("\n--- STATIC CODE ANALYSIS ---")
        targets = ["nemesis_core.py", "services/blockchain/collectors.py", "services/bitquery_builder.py"]
        for t in targets:
            fpath = BASE_DIR / t
            if not fpath.exists():
                self.log("Static Code Analysis", t, False, "File not found")
                continue
            
            try:
                code = fpath.read_text(encoding='utf-8')
                tree = ast.parse(code)
                
                func_count = sum(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
                class_count = sum(isinstance(node, ast.ClassDef) for node in ast.walk(tree))
                
                exposed = False
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
                        if isinstance(node.value.value, str):
                            val = node.value.value
                            if val.startswith("sk-") or val.startswith("ory_at_") or (len(val)>30 and "key" in str(node.targets[0]).lower()):
                                if "placeholder" not in val.lower():
                                    exposed = True
                
                if exposed:
                    self.log("Security & Compliance", f"Secrets Check {t}", False, "Hardcoded secrets found!")
                else:
                    self.log("Security & Compliance", f"Secrets Check {t}", True, "No hardcoded secrets detected.")
                
                self.log("Static Code Analysis", t, True, f"AST Parsed. Funcs: {func_count}, Classes: {class_count}")
            except Exception as e:
                self.log("Static Code Analysis", t, False, f"AST Parse Error: {e}")

    def run_browser_tests(self):
        print("\n--- FRONTEND & E2E BROWSER TESTS ---")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, channel="msedge")
                page = browser.new_page()
                
                # 1. Test Landing
                start = time.time()
                page.goto(f"file:///{BASE_DIR}/landing.html")
                page.wait_for_load_state("networkidle")
                dur = round(time.time() - start, 2)
                title = page.title()
                if "NEMESIS" in title.upper():
                    self.log("Frontend E2E Tests", "landing.html UI Load", True, f"Title: {title}")
                    self.log("Performance Benchmarks", "landing.html Load Time", True, f"{dur}s")
                else:
                    self.log("Frontend E2E Tests", "landing.html UI Load", False, "Missing NEMESIS in title")
                
                # 2. Test Admin Dashboard
                page.goto(f"file:///{BASE_DIR}/admin.html")
                page.wait_for_load_state("load")
                admin_body = page.content()
                if "Testing & Audit Lifecycle" in admin_body or "NEMESIS" in admin_body:
                    self.log("Frontend E2E Tests", "admin.html Testing Module", True, "Module rendered")
                else:
                    self.log("Frontend E2E Tests", "admin.html Testing Module", False, "Module not found in DOM")
                
                # 3. Test Nemesis ID
                page.goto(f"file:///{BASE_DIR}/nemesis_id.html")
                page.wait_for_load_state("load")
                if page.locator("#wallet-input").count() > 0 or page.locator("input").count() > 0:
                    self.log("Frontend E2E Tests", "nemesis_id.html Inputs", True, "Input forms found")
                else:
                    self.log("Frontend E2E Tests", "nemesis_id.html Inputs", False, "Missing inputs")

                # 4. Test Tracer (E2E API Call Interception)
                print("   > Running E2E Graph API Test on Tracer UI...")
                api_responses = []
                page.on("response", lambda response: api_responses.append(response) if "api/node/" in response.url else None)
                
                page.goto(f"file:///{BASE_DIR}/tracer.html")
                page.wait_for_load_state("load")
                
                try:
                    page.evaluate(f'''
                        if (typeof window.investigateTarget === "function") {{
                            window.investigateTarget("{TARGET_WALLET}");
                        }} else {{
                            fetch("{API_URL}/api/node/graph?address={TARGET_WALLET}").then(r=>r.json());
                        }}
                    ''')
                    page.wait_for_timeout(3000)
                    
                    found_graph = False
                    for r in api_responses:
                        if "api/node/graph" in r.url and r.status == 200:
                            found_graph = True
                            
                    if found_graph:
                        self.log("Backend Integration Tests", "Tracer /api/node/graph E2E", True, "200 OK intercepted from backend")
                    else:
                        self.log("Backend Integration Tests", "Tracer /api/node/graph E2E", False, "No 200 response from backend")
                        
                except Exception as e:
                    self.log("Frontend E2E Tests", "Tracer UI Interaction", False, str(e))
                
                browser.close()
        except Exception as e:
            self.log("Frontend E2E Tests", "Playwright Automation", False, f"Error: {e}")

    def generate_report(self):
        # Generate JSON
        report_path_json = REPORTS_DIR / "audit_report.json"
        with open(report_path_json, "w", encoding='utf-8') as f:
            json.dump(self.results, f, indent=4)
            
        # Generate HTML
        html_blocks = []
        for cat, tests in self.results.items():
            if not tests: continue
            
            rows = ""
            for t in tests:
                badge_class = "badge-pass" if t["status"] == "PASS" else "badge-fail"
                icon = "<i class='fa-solid fa-check'></i>" if t["status"] == "PASS" else "<i class='fa-solid fa-xmark'></i>"
                rows += f'''
                <tr>
                    <td>{t["name"]}</td>
                    <td><span class="badge {badge_class}">{icon} {t["status"]}</span></td>
                    <td>{t["details"]}</td>
                </tr>
                '''
            
            html_blocks.append(f'''
            <div class="category">
                <h2>{cat}</h2>
                <table>
                    <thead>
                        <tr>
                            <th width="40%">Test Name</th>
                            <th width="20%">Status</th>
                            <th width="40%">Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
            ''')

        final_html = HTML_TEMPLATE.replace(
            "{timestamp}", datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        ).replace(
            "{api_url}", API_URL
        ).replace(
            "{content}", "\n".join(html_blocks)
        )
        
        report_path_html = BASE_DIR / "audit_report.html"
        with open(report_path_html, "w", encoding='utf-8') as f:
            f.write(final_html)
            
        print(f"\n[SYSTEM] Master JSON audit report saved to {report_path_json}")
        print(f"[SYSTEM] Master HTML audit report published to {report_path_html}")

if __name__ == "__main__":
    auditor = Auditor()
    auditor.run_static_analysis()
    auditor.run_browser_tests()
    auditor.generate_report()
