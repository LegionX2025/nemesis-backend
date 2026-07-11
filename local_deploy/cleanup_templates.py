import os
import glob

template_dir = r"c:\Users\LEGIONX\Downloads\cases\local_deploy\frontend\templates"

keep_files = [
    "index.html",
    "nemesis_id_landing.html",
    "nemesis_id_new.html",
    "nemesis_tracer.html",
    "wrangler.toml",
    "_redirects"
]

def clean_templates():
    if not os.path.exists(template_dir):
        print(f"Template directory not found: {template_dir}")
        return

    print(f"Cleaning up {template_dir}...")
    deleted = 0
    for file_path in glob.glob(os.path.join(template_dir, "*.*")):
        basename = os.path.basename(file_path)
        if basename not in keep_files and os.path.isfile(file_path):
            try:
                os.remove(file_path)
                print(f"Deleted: {basename}")
                deleted += 1
            except Exception as e:
                print(f"Error deleting {basename}: {e}")
                
    print(f"Cleanup complete. Deleted {deleted} files.")

if __name__ == "__main__":
    clean_templates()
