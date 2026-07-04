import os
import glob
import shutil

src_dir = r"C:\Users\LEGIONX\.gemini\antigravity-ide\brain\32b5dd40-02fd-438b-b76a-775d8d4a6594"
dst_dir = r"C:\Users\LEGIONX\Downloads\cases\local_deploy\assets\icons"

os.makedirs(dst_dir, exist_ok=True)

targets = ["nemesis_wallet_icon", "nemesis_contract_icon", "nemesis_alert_icon", "nemesis_mixer_icon"]

for target in targets:
    files = glob.glob(os.path.join(src_dir, f"{target}_*.png"))
    if files:
        # Take the most recently created one if multiple
        latest_file = max(files, key=os.path.getctime)
        shutil.copy(latest_file, os.path.join(dst_dir, f"{target}.png"))
        print(f"Copied {target}")
    else:
        print(f"Could not find files for {target}")

print("Done")
