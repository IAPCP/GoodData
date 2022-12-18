import os
import sys
from tqdm.auto import tqdm

def consolidate_project(project_path: str):
    if not os.path.exists(os.path.join(project_path, "bin")):
        return
    os.system(f"cp -r {os.path.join(project_path, 'bin')} {os.path.join(project_path, 'bin_ida')}")
    for file in os.listdir(os.path.join(project_path, "bin")):
        if file.endswith(".decomp") or \
            file.endswith(".log") or \
            file.endswith(".i64") or \
            file.endswith(".id0") or \
            file.endswith(".id1") or \
            file.endswith(".id2") or \
            file.endswith(".nam") or \
            file.endswith(".til") or \
            file.endswith(".idb"):
            os.system(f"rm -f {os.path.join(project_path, 'bin', file)}")

for project in tqdm(os.listdir(sys.argv[1])):
    consolidate_project(os.path.join(sys.argv[1], project))
            