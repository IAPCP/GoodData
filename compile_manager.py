#!/usr/bin/env python3
import json
import os
import shutil
import docker
import logging
import enum
import multiprocessing
import time
import atexit

IMAGE = "hook_build"
COMPILE_SCRIPT = "/root/compile.sh"

PackageStatus = enum.Enum("PackageStatus", ("NOT_STARTED", "EXIT_EARLY", "DONE", "ERROR"))

def do_compile(package_name, path):
    logger = logging.getLogger(package_name)
    logger.setLevel(logging.DEBUG)
    logger.info(f"Start compiling package {package_name}")
    save_path = os.path.join(path, package_name)
    logger.debug(f"Checking if path {save_path} exists")
    assert (not os.path.exists(save_path))
    logger.debug(f"Creating path {save_path}")
    os.system(f"mkdir -p {save_path}")
    logger.info(f"Compiling in docker")
    client = docker.from_env()
    log_path = os.path.join(save_path, "compile.log")
    try:
        result = client.containers.run(image='hook_build', command=f'{COMPILE_SCRIPT} {package_name}', remove=True, volumes={save_path: {'bind': '/root/package', 'mode': 'rw'}})
    except Exception as e:
        with open(os.path.join(save_path, 'error'), 'w') as f:
            f.write(str(e))
            return
    logger.info(f"Compile complete, saving log to {log_path}")
    with open(log_path, "wb") as f:
        f.write(result)
    os.system(f"touch {os.path.join(save_path, 'done')}")

def package_status(package_name, path):
    save_path = os.path.join(path, package_name)
    if not os.path.exists(save_path):
        return PackageStatus.NOT_STARTED
    if os.path.exists(os.path.join(save_path, "done")):
        return PackageStatus.DONE
    if os.path.exists(os.path.join(save_path, "error")):
        return PackageStatus.ERROR
    return PackageStatus.EXIT_EARLY

def compile_package(package_name, path):
    logger = logging.getLogger(__file__)
    logger.setLevel(logging.DEBUG)
    status = package_status(package_name, path)
    if status == PackageStatus.NOT_STARTED:
        do_compile(package_name, path)
    elif status == PackageStatus.EXIT_EARLY:
        logger.info(f"{package_name} exited early, remove and recompile")
        shutil.rmtree(os.path.join(path, package_name))
        do_compile(package_name, path)
    elif status == PackageStatus.DONE or status == PackageStatus.ERROR:
        logger.info(f"{package_name} already compiled, skip")
    else:
        logger.error(f"{package_name} status unknown")

def compile_list_serially(json_path, path):
    logger = logging.getLogger(__file__)
    logger.setLevel(logging.DEBUG)
    logger.info("SERIAL MODE")
    logger.info("Start compiling list")
    logger.info("Reading compile list")
    with open(json_path) as f:
        package_list = json.load(f)
    logger.debug(f"{len(package_list)} packages to compile")
    for package in package_list:
        package_name = package['package']
        compile_package(package_name, path)

def compile_list_worker(queue, path, idx):
    logger = logging.getLogger(__file__)
    logger.setLevel(logging.DEBUG)
    logger.info(f"Start worker {idx}")
    while True:
        try:
            package_name = queue.get()
        except multiprocessing.Queue.Empty:
            logger.info(f"Worker {idx} meet queue empty, sleep")
            time.sleep(2)
        logger.info(f"Worker {idx} fetching package {package_name}, begin compile")
        compile_package(package_name, path)

def compile_list_parallel(json_path, path, max_worker=10):
    logger = logging.getLogger(__file__)
    logger.setLevel(logging.DEBUG)
    logger.info("SERIAL MODE")
    logger.info("Start compiling list")
    logger.info("Reading compile list")
    with open(json_path) as f:
        package_list = json.load(f)
    logger.debug(f"{len(package_list)} packages to compile")
    manager = multiprocessing.Manager()
    queue = manager.Queue(max_worker)
    pool = multiprocessing.Pool(max_worker)
    for idx in range(max_worker):
        pool.apply_async(compile_list_worker, (queue, path, idx))
    for package in package_list:
        package_name = package['package']
        qsize = queue.qsize()
        while True:
            if qsize > max_worker * 5:
                time.sleep(2)
            else:
                logger.info(f"Queue size {qsize}, put package {package_name}")
                queue.put(package_name)
                break
    pool.close()
    pool.join()

@atexit.register
def clear_container():
    logger = logging.getLogger("clear_container")
    logger.setLevel(logging.DEBUG)
    logger.info("Begin clearing containers")
    client = docker.from_env()
    for container in client.containers.list(all=True):
        if container.image.tags[0].split(':')[0] == IMAGE:
            logger.info(f"Removing container {container.id}")
            container.remove(force=True)

if __name__ == '__main__':
    # manager_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "compile_manager.log")
    manager_log_path = "./compile_manager.log"
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename=manager_log_path)
    # logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    import sys 
    compile_list_parallel(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))