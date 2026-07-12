import os, glob

base_dir = 'C:/Users/LEGIONX/Downloads/cases/nemesis_project/templates'
files = glob.glob(os.path.join(base_dir, '**/*.html'), recursive=True)

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Replace WS
    content = content.replace('wsUrl = `ws://${window.location.host}`', 'wsUrl = window.location.hostname.includes(\'localhost\') || window.location.hostname.includes(\'127.0.0.1\') ? `ws://${window.location.host}` : `wss://nemesis-backend.onrender.com`;')
    content = content.replace('protocol + window.location.host + "/ws/"', '(window.location.hostname.includes(\'localhost\') || window.location.hostname.includes(\'127.0.0.1\') ? protocol + window.location.host + "/ws/" : "wss://nemesis-backend.onrender.com/ws/")')
    content = content.replace('${protocol}//${window.location.host}/api/', '${window.location.hostname.includes(\'localhost\') ? protocol + \'//\' + window.location.host : \'https://nemesis-backend.onrender.com\'}/api/')
    
    # Replace fetch
    content = content.replace('fetch(\'/api/', 'fetch( (window.location.hostname.includes(\'localhost\') || window.location.hostname.includes(\'127.0.0.1\') ? \'\' : \'https://nemesis-backend.onrender.com\') + \'/api/')
    content = content.replace('fetch(`/api/', 'fetch(`${window.location.hostname.includes(\'localhost\') || window.location.hostname.includes(\'127.0.0.1\') ? \'\' : \'https://nemesis-backend.onrender.com\'}/api/')
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)
print('Patched API endpoints.')
