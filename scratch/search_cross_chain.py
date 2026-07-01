import os

def search_in_file(filepath, query):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for i, line in enumerate(f):
            if query.lower() in line.lower():
                print(f"{filepath}:{i+1}: {line.strip()}")

search_in_file("app.py", "cross_chain")
search_in_file("case.py", "cross_chain")
search_in_file("main.py", "cross_chain")
