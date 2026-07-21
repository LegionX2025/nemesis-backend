import sys
import traceback

try:
    with open('C:/Users/LEGIONX/Downloads/cases/darknet/darknetv2.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Lines 797 to 832 (0-indexed 796 to 831)
    for i in range(796, 832):
        if lines[i].startswith("    "):
            lines[i] = lines[i][4:]

    with open('C:/Users/LEGIONX/Downloads/cases/darknet/darknetv2.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Fixed indentation in darknetv2.py successfully.")
except Exception as e:
    print("Error fixing darknetv2.py:", e)
    traceback.print_exc()

