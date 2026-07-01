import re

with open("C:/Users/LEGIONX/downloads/cases/templates/index.html", "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if "png" in line or "logo" in line:
            print(f"{i+1}: {line.strip()}")
