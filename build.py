# build.py
#
# Builds the application with PyInstaller and packages all resources into a ZIP file.

from main import APP_NAME, APP_VERSION

new_executable_name = f"{APP_NAME.replace(' ', '')}_{APP_VERSION}"

import os
import shutil

# build EXE
os.system(f"pyinstaller -F main.py --windowed --noconsole --icon=assets/icon.ico") 

# setup folders if they don't exist

if not os.path.exists("./output"):
    os.makedirs("./output")
if not os.path.exists("./pkg"):
    os.makedirs("./pkg")
if not os.path.exists("./output/thirdparty"):
    os.makedirs("./output/thirdparty")

# move the executable
shutil.move(f"./dist/main.exe", f"./output/BlueThinnerLite.exe")
# copy the thirdparty folder
shutil.copytree("./thirdparty", "./output/thirdparty", dirs_exist_ok=True)
# copy the assets folder
shutil.copytree("./assets", "./output/assets", dirs_exist_ok=True)

# zip the output folder into ./new_executable_name.zip
shutil.make_archive(f"./pkg/{new_executable_name}", 'zip', "./output")

# remove the output folder
shutil.rmtree("./output")