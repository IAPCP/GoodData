#!/usr/bin/env python3
import os
import sys
import shutil

REMOVE = False

source_path = os.path.abspath(sys.argv[1])
target_path = os.path.abspath(sys.argv[2])

packages = os.listdir(source_path)
for package in packages:
    package_path = os.path.join(source_path, package)
    if os.path.exists(f"{package_path}/done") or os.path.exists("{package_path}/error"):
        
        if os.path.exists(f"{package_path}/fake"):
            print("Skipping fake package {}".format(package))
            continue
        
        print("Copying package {}".format(package))
        os.system("cp -r {} {}".format(package_path, target_path))
        
        print("Removing package {}".format(package))
        shutil.rmtree(package_path)