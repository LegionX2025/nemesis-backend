import sys

with open(r"C:\Users\LEGIONX\downloads\cases\services\trace_engine.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i in range(634, 799):
    if lines[i].startswith("            "):
        lines[i] = lines[i][4:]

with open(r"C:\Users\LEGIONX\downloads\cases\services\trace_engine.py", "w", encoding="utf-8") as f:
    f.writelines(lines)
print("Indentation fixed.")
