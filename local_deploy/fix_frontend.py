import os
import re
import shutil

FRONTEND_DIR = r"c:\Users\LEGIONX\Downloads\cases\local_deploy\frontend"
ARCHIVE_DIR = os.path.join(FRONTEND_DIR, "archive")

def run_fix():
    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR)

    # Known redundant files
    redundant_files = [
        "nemesis_id.html",
        "nemesis_id_dashboard.html",
        "nemesis_tracer.html",
        "nemesis_tracer.html.html",
        "intro.html",
        "nemesis_butterfly.html",
        "nemesis_final_audit.html",
        "project_nemesis.html",
        "cloudflare_ops.html",
        "nemesis_fullscreen_dashboard.html"
    ]

    # Move redundant files
    for file in redundant_files:
        src = os.path.join(FRONTEND_DIR, file)
        dst = os.path.join(ARCHIVE_DIR, file)
        if os.path.exists(src):
            shutil.move(src, dst)
            print(f"Moved {file} to archive.")

    # Fix remaining HTML files
    for root, _, files in os.walk(FRONTEND_DIR):
        if "archive" in root or "_cf_pages_dist" in root or "tracer_app" in root:
            continue

        for file in files:
            if file.endswith(".html"):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                original_content = content

                # Ensure tailwind
                if "cdn.tailwindcss.com" not in content and "</head>" in content:
                    content = content.replace("</head>", '    <script src="https://cdn.tailwindcss.com"></script>\n</head>')
                
                # Remove autofixer if present
                content = re.sub(r'<script[^>]*autofixer[^>]*></script>', '', content)
                content = re.sub(r'<script[^>]*src=["\']/assets/autofixer[^>]*></script>', '', content)
                
                # Fix links
                content = content.replace('href="nemesis_id.html"', 'href="nemesis_id_landing.html"')
                content = content.replace('href="/nemesis_id.html"', 'href="/nemesis_id_landing.html"')
                
                content = content.replace('href="nemesis_tracer.html"', 'href="nemesis_tracer_landing.html"')
                content = content.replace('href="/nemesis_tracer.html"', 'href="/nemesis_tracer_landing.html"')

                if content != original_content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Fixed {file}")

if __name__ == "__main__":
    run_fix()
    print("Frontend fix completed.")
