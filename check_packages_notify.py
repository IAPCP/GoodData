#!/usr/bin/env python3
from package_utils import *
import sys
import os
from urllib.parse import quote

def bark_webhook(bark_id, content):
    os.system(f"curl https://api.day.app/{bark_id}/{quote('Compile Status')}/{quote(content)}")
    
def main(path, bark_id):
    exists_packages = os.listdir(path)
    success = 0
    error = 0
    compiling = 0
    use_gcc = 0
    
    total = len(exists_packages)
    
    for package in exists_packages:
        status = package_status(package, path)
        if status == PackageStatus.DONE:
            success += 1
            if package_use_gcc(package, path):
               use_gcc += 1 
        elif status == PackageStatus.ERROR:
            error += 1
        elif status == PackageStatus.EXIT_EARLY:
            compiling += 1
        else:
            pass
    
    bark_webhook(bark_id, f"{total} in total, {success} success, {error} error, {compiling} compiling, {use_gcc} of {success} use gcc")


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])