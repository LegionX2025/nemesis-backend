import os

def tail(filename, n=50):
    if not os.path.exists(filename):
        return f"File {filename} not found."
    
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        # Seek to the end of the file
        f.seek(0, os.SEEK_END)
        file_size = f.tell()
        
        # Buffer size
        block_size = 1024
        blocks = []
        lines_found = 0
        position = file_size
        
        while position > 0 and lines_found < n:
            read_size = min(block_size, position)
            position -= read_size
            f.seek(position)
            block = f.read(read_size)
            lines_found += block.count('\n')
            blocks.insert(0, block)
            
        return "".join(blocks).splitlines()[-n:]

print("=== LAST 20 LINES OF DEPLOY.LOG ===")
for line in tail("C:/Users/LEGIONX/Downloads/cases/nemesis_project/logs/deploy.log", 20):
    print(line)

print("\n=== LAST 20 LINES OF NEMESIS.LOG ===")
for line in tail("C:/Users/LEGIONX/Downloads/cases/nemesis_project/logs/nemesis.log", 20):
    print(line)
