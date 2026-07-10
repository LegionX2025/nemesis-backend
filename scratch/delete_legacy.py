import os
import glob

files = glob.glob('LFR_*.csv') + glob.glob('LFR_*.json')
for f in files:
    try:
        os.remove(f)
        print(f"Deleted {f}")
    except Exception as e:
        print(f"Failed to delete {f}: {e}")
