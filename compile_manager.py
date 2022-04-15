import json
import os
import shutil
import docker
import logging

IMAGE = "hook_build"
COMPILE_SCRIPT = "/root/compile.sh"

def do_compile(package_name, path):
    save_path = os.path.join(path, package_name)
    assert (not os.path.exists(save_path))
    os.system(f"mkdir -p {save_path}")
    client = docker.from_env()
    client.containers.run(image='hook_build', command=f'{COMPILE_SCRIPT} {package_name}', remove=True)
    os.system(f"touch {os.path.join(save_path, 'done')}")

if __name__ == '__main__':
    do_compile("alltray", "/home/kongjiadongyuan/build_database")