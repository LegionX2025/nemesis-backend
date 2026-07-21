import shutil

src = r"c:\Users\LEGIONX\Downloads\nemesis\tracer_scripts\public\nemesis_id_new.html"
dst = r"c:\Users\LEGIONX\Downloads\cases\local_deploy\frontend\nemesis_id_new.html"

shutil.copy2(src, dst)
print("Copied successfully.")
