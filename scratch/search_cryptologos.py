import os

def search_dir(dir_path, query):
    for root, _, files in os.walk(dir_path):
        for f in files:
            if f.endswith(('.html', '.js', '.py')):
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8') as file:
                        for i, line in enumerate(file):
                            if query.lower() in line.lower():
                                print(f"{path}:{i+1}:{line.strip()}")
                except:
                    pass

search_dir(r"C:\Users\LEGIONX\downloads\cases", "cryptologos")
