import os
import sys
import binaryninja as bn
from tqdm.auto import tqdm

def analyze_binary(file_path: str):
    file_name = os.path.basename(file_path)
    dir_path = os.path.dirname(file_path)
    if file_name.endswith(".bndb"):
        return
    else:
        if os.path.exists(os.path.join(dir_path, file_name + ".bndb")):
            return
        else:
            for _ in range(3):
                bv = bn.open_view(file_path)
                succeed = bv.create_database(os.path.join(dir_path, file_name + ".bndb"))
                if succeed:
                    break

def analyze_package(package_path: str):
    if not os.path.exists(os.path.join(package_path, "bin_ninja")):
        os.system(f"cp -r {os.path.join(package_path, 'bin')} {os.path.join(package_path, 'bin_ninja')}")
    for file in os.listdir(os.path.join(package_path, "bin_ninja")):
        file_path = os.path.join(package_path, "bin_ninja", file)
        analyze_binary(file_path)


if __name__ == '__main__':
    for package_name in tqdm(os.listdir(sys.argv[1])):
        package_path = os.path.join(sys.argv[1], package_name)
        analyze_package(package_path)