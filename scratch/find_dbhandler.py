import sys

def find_dbhandler():
    with open("C:\\Users\\LEGIONX\\Downloads\\cases\\darknet\\darknetv2.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        if "class DBHandler" in line:
            print(f"Found DBHandler at line {i+1}")
            break

if __name__ == "__main__":
    find_dbhandler()
