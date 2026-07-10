import os
import sys

def search_dir(d, target):
    for root, _, files in os.walk(d):
        for f in files:
            if f.endswith('.html') or f.endswith('.js') or f.endswith('.py'):
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8') as file:
                        for i, line in enumerate(file):
                            if target in line:
                                print(f"{path}:{i+1}:{line.strip()}")
                except Exception as e:
                    pass

search_dir('.', 'avoidOverlap')
