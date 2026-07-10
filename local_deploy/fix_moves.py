import os
import shutil

root_dir = r"C:\Users\LEGIONX\Downloads\cases\local_deploy"

def move_contents(src_dir, dst_dir):
    src_path = os.path.join(root_dir, src_dir)
    dst_path = os.path.join(root_dir, dst_dir)
    
    if os.path.exists(src_path) and os.path.isdir(src_path):
        for item in os.listdir(src_path):
            s = os.path.join(src_path, item)
            d = os.path.join(dst_path, item)
            try:
                shutil.move(s, d)
                print(f"Moved: {s} -> {d}")
            except Exception as e:
                print(f"Error moving {s}: {e}")
        # Remove the now-empty original directory
        try:
            os.rmdir(src_path)
            print(f"Removed empty directory: {src_path}")
        except Exception as e:
            print(f"Could not remove {src_path}: {e}")
    else:
        print(f"Skip: {src_path} not found or not a directory.")

move_contents("services", "backend/app/services")
move_contents("scripts", "backend/scripts")
move_contents("tests", "backend/tests")
