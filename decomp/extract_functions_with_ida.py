#!/usr/bin/env python3

import os
import sys
import time
from tqdm.auto import tqdm
import multiprocessing


def analyze(bin_path, retry=3):
    tried = 0
    while tried < retry:
        try:
            bin_dir_path = os.path.dirname(bin_path)
            bin_name = os.path.basename(bin_path)
            os.system(
                f'idat64 -A -S"ida_script/dump_pseudocode.py {bin_dir_path}" -L{os.path.join(bin_dir_path, bin_name+".log")} {bin_path}')
        except Exception:
            pass
        if os.path.exists(os.path.join(bin_dir_path, bin_name+".decomp")):
            break
        else:
            tried += 1
    os.system(f"rm -f {os.path.join(bin_dir_path, bin_name+'.id0')}")
    os.system(f"rm -f {os.path.join(bin_dir_path, bin_name+'.id1')}")
    os.system(f"rm -f {os.path.join(bin_dir_path, bin_name+'.id2')}")
    os.system(f"rm -f {os.path.join(bin_dir_path, bin_name+'.nam')}")
    os.system(f"rm -f {os.path.join(bin_dir_path, bin_name+'.til')}")


project_path = sys.argv[1]

pool = multiprocessing.Pool(56)
for package in tqdm(os.listdir(project_path)):
    for binary in os.listdir(os.path.join(project_path, package, "bin")):
        if binary.endswith(".decomp") or \
            binary.endswith(".log") or \
            binary.endswith(".i64"):
            continue
        if binary.endswith(".id0") or \
            binary.endswith(".id1") or \
            binary.endswith(".id2") or \
            binary.endswith(".nam") or \
            binary.endswith(".til"):
            os.system(f"rm -f {os.path.join(project_path, package, 'bin', binary)}")
            continue
        if os.path.exists(os.path.join(project_path, package, "bin", binary+".decomp")):
            continue
        pool.apply_async(analyze, (os.path.join(
            project_path, package, "bin", binary), ))

pool.close()


while True:
    oknum = 0
    totalnum = 0
    for package in os.listdir(project_path):
        for binary in os.listdir(os.path.join(project_path, package, "bin")):
            if binary.endswith(".decomp") or \
                binary.endswith(".log") or \
                binary.endswith(".i64") or \
                binary.endswith(".id0") or \
                binary.endswith(".id1") or \
                binary.endswith(".id2") or \
                binary.endswith(".nam") or \
                binary.endswith(".til"):
                continue
            if os.path.exists(os.path.join(project_path, package, "bin", binary+".decomp")):
                oknum += 1
            totalnum += 1
    print(f"{oknum}/{totalnum} ({oknum/totalnum*100:.2f}%)")
    time.sleep(10)


pool.join()
