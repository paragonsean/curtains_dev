import os
import platform
import shutil
import sys
import importlib.util 

# Run at least once before using PyInstaller/Flet pack to create an .exe file

def patch_pyinjector():
    """A patch to make pyinjector work with PyInstaller"""
    patch_code = ['import platform\n',
                  '\n',
                  '# Patch code for PyInstaller: Detect if frozen to find the right pyd binary\n',
                  "if getattr(sys, 'frozen', False):\n",
                  '    os_bit = platform.machine().lower()\n',
                  "    py_runtime = str(sys.version[0:4]).replace('.', '')\n",
                  "    bin_name = f'libinjector.cp{py_runtime}-win_{os_bit}.pyd'\n",
                  "    libinjector_path = os.path.join(sys._MEIPASS, 'assets') + '\' + bin_name\n",
                  'else:\n',
                  "    libinjector_path = find_spec('.libinjector', __package__).origin\n"]
    spec = importlib.util.find_spec("pyinjector")
    pyfile_path = spec.submodule_search_locations[0] + r'\api.py'

    with open(pyfile_path, "r") as f_r:
        contents = f_r.readlines()
        if contents[5:16] == patch_code:
            print('Skip patching. pyinjector.py has already been patched')
        else:
            contents.insert(0, "import sys\n")
            contents.insert(6, "#")
            patch_code.reverse()
            for line in patch_code:
                contents.insert(5, line)

            with open(pyfile_path, "w") as f_w:
                contents = "".join(contents)
                f_w.write(contents)
            print('pyinjector.py has been patched successfully')

def copy_binary_to_assets():
    """Copy the libinjector binary to assets folder for freezing with PyInstaller"""
    # Specify the path to the libinjector binary
    libinjector_source_path = r'C:\Users\\spocam\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\pyinjector\\injector.cp311-win_amd64.pyd'
    
    # Specify the path to the assets folder where the binary will be copied
    basedir = os.path.dirname(os.path.abspath(__file__))
    assets_path = os.path.join(basedir, "assets")
    
    # Copy the binary to the assets folder
    shutil.copy(libinjector_source_path, assets_path)
    print('libinjector pyd-file has been copied to the assets folder')

if __name__ == "__main__":
    patch_pyinjector()
    copy_binary_to_assets()
