#!/usr/bin/env python3
from package_utils import *
import shutil
import sys
import os


def main(path):
    packages = os.listdir(path)
    for package in packages:
        status = package_status(package, path)
        if status == PackageStatus.EXIT_EARLY or status == PackageStatus.ERROR:
            print(f"Removing package {package}")
            shutil.rmtree(os.path.join(path, package))
            print(f"{package} remove ok")

if __name__ == '__main__':
    main(sys.argv[1])
            
