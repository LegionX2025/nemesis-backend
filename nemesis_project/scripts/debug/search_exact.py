import os

search_string = "Playwright fallback failed"
root_dir = r"C:\Users\LEGIONX\Downloads\cases\nemesis_project"

for subdir, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(subdir, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if search_string in line:
                            print(f"{filepath}:{line_num}: {line.strip()}")
            except Exception:
                pass
