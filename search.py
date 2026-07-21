with open('c:/Users/LEGIONX/Downloads/cases/templates/index.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'Evidentiary Transaction' in line or 'transaction-list' in line:
            print(f"{i+1}: {line.strip()}")
