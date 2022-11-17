#!/usr/bin/env python3
from package_utils import *
import sys
import os
import time
import tensorboardX
from urllib.parse import quote

logpath = os.path.join('/home/kongjiadongyuan', 'tb_logs', 'compile_status')

def bark_webhook(bark_id, content):
    os.system(f"curl https://api.day.app/{bark_id}/{quote('Compile Status')}/{quote(content)}")
    
def main(path, bark_id = None):
    exists_packages = os.listdir(path)
    success = 0
    error = 0
    compiling = 0
    use_gcc = 0
    
    total = len(exists_packages)
    
    
    not_using_gcc = []
    for package in exists_packages:
        status = package_status(package, path)
        if status == PackageStatus.DONE:
            success += 1
            if package_use_gcc(package, path):
               use_gcc += 1 
            else:
                not_using_gcc.append(package)
        elif status == PackageStatus.ERROR:
            error += 1
        elif status == PackageStatus.EXIT_EARLY:
            compiling += 1
        else:
            pass
    writer = tensorboardX.SummaryWriter(logpath)    
    writer.add_scalars('compile_status', {'success': success, 'error': error, 'compiling': compiling, 'total': total}, time.time()-1653204170)
    if bark_id is None:
        print(f"{total} in total, {success} success, {error} error, {compiling} compiling, {use_gcc} of {success} use gcc")
        # print(not_using_gcc)
    else:
        bark_webhook(bark_id, f"{total} in total, {success} success, {error} error, {compiling} compiling, {use_gcc} of {success} use gcc")


if __name__ == '__main__':
    if len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    if len(sys.argv) == 2:
        main(sys.argv[1])
