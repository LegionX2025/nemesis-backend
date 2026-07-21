import shutil
import os

def zip_project():
    source_dir = os.path.dirname(os.path.abspath(__file__))
    zip_name = "nemesis_v32"
    
    print(f"Zipping contents of {source_dir}...")
    try:
        shutil.make_archive(zip_name, 'zip', source_dir)
        print(f"Successfully created {zip_name}.zip in {source_dir}")
    except Exception as e:
        print(f"Error creating zip file: {e}")

if __name__ == "__main__":
    zip_project()
