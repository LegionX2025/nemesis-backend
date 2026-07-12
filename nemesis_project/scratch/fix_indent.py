with open('services/scraper_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Indent lines 389 to 478 (0-indexed 388 to 477)
for i in range(388, 478):
    if lines[i].strip(): # Only indent non-empty lines, though indenting empty ones doesn't hurt Python
        lines[i] = "    " + lines[i]

with open('services/scraper_engine.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
