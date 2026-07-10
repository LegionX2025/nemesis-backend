import os
import glob

search_dir = r"C:\Users\LEGIONX\downloads\cases"
for ext in ["*.py", "*.html", "*.js"]:
    for file in glob.glob(os.path.join(search_dir, "**", ext), recursive=True):
        if "venv" in file or ".git" in file:
            continue
        try:
            with open(file, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if "coinbase" in line.lower():
                        print(f"{file}:{i+1}: {line.strip()}")
        except Exception:
            pass
