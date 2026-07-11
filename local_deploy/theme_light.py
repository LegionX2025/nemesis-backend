import os

files_to_light_theme = [
    r"c:\Users\LEGIONX\Downloads\cases\local_deploy\frontend\templates\nemesis_id_new.html",
    r"c:\Users\LEGIONX\Downloads\cases\local_deploy\frontend\templates\nemesis_id_landing.html",
    r"c:\Users\LEGIONX\Downloads\cases\local_deploy\frontend\templates\nemesis_id.html"
]

replacements = {
    "bg-slate-900": "bg-slate-50",
    "bg-slate-800": "bg-white",
    "bg-slate-950": "bg-slate-100",
    "text-slate-200": "text-slate-800",
    "text-slate-300": "text-slate-700",
    "text-slate-400": "text-slate-600",
    "text-white": "text-slate-900",
    "border-slate-700": "border-slate-200",
    "border-slate-800": "border-slate-300",
    "ring-slate-700": "ring-slate-200",
    "bg-slate-700": "bg-slate-200",
    "text-slate-100": "text-slate-900"
}

for file_path in files_to_light_theme:
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        for dark, light in replacements.items():
            content = content.replace(dark, light)
            
        # Also fix any particles.js colors if present to be visible on light theme
        content = content.replace('"color":{"value":"#ffffff"}', '"color":{"value":"#334155"}')
        content = content.replace('"line_linked":{"enable":true,"distance":150,"color":"#ffffff"', '"line_linked":{"enable":true,"distance":150,"color":"#475569"')

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Applied light theme to: {file_path}")

