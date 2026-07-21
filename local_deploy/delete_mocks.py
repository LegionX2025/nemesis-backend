import os
import shutil

base_dir = r"C:\Users\LEGIONX\Downloads\cases\local_deploy"

def rm_file(path):
    p = os.path.join(base_dir, path)
    if os.path.exists(p):
        os.remove(p)
        print(f"Removed {p}")

def rm_dir(path):
    p = os.path.join(base_dir, path)
    if os.path.exists(p):
        shutil.rmtree(p)
        print(f"Removed {p}")

rm_dir(r"frontend\mock_suite")
rm_dir(r"frontend\mock_designs")
rm_file("generate_suite_themes.py")
rm_file("generate_enterprise_themes.py")
rm_file("generate_fullscreen_themes.py")
