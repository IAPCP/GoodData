#!/usr/bin/env python3
import os
import sys

def project_ok(project_path: str):
    if (not os.path.exists(os.path.join(project_path, "bin"))) or (len(os.listdir(os.path.join(project_path, "bin"))) == 0):
        return False
    else:
        return True

dir_path = sys.argv[1]
for package_name in os.listdir(dir_path):
    if project_ok(os.path.join(dir_path, package_name)):
        pass
    else:
        os.system(f"rm -r {os.path.join(dir_path, package_name)}")