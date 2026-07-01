import re

with open("C:/Users/LEGIONX/downloads/cases/templates/index.html", "r", encoding="utf-8") as f:
    content = f.read()

ws_lines = [line for line in content.split("\n") if "WebSocket" in line or "/ws/" in line]
for line in ws_lines:
    print(line.strip())
