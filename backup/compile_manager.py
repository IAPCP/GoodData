#!/usr/bin/env python3
import json
import os
import shutil
import docker
import logging
import multiprocessing
import time
import atexit
from package_utils import *

IMAGE = "hook_build:9.3.0"
COMPILE_SCRIPT = "/root/compile.sh"



def do_compile(package_name, path, logger):
    save_path = os.path.join(path, package_name)
    logger.debug(f"Checking if path {save_path} exists")
    assert (not os.path.exists(save_path))
    logger.debug(f"Creating path {save_path}")
    os.system(f"mkdir -p {save_path}")
    logger.info(f"Compiling in docker")
    client = docker.from_env()
    log_path = os.path.join(save_path, "compile.log")
    try:
        result = client.containers.run(image=IMAGE, command=f'{COMPILE_SCRIPT} {package_name}', remove=True, volumes={save_path: {'bind': '/root/package', 'mode': 'rw'}})
    except Exception as e:
        with open(os.path.join(save_path, 'error'), 'w') as f:
            f.write(str(e))
            return
    logger.info(f"Compile complete, saving log to {log_path}")
    with open(log_path, "wb") as f:
        f.write(result)
    os.system(f"touch {os.path.join(save_path, 'done')}")



def compile_package(package_name, path, logger):
    status = package_status(package_name, path)
    if status == PackageStatus.NOT_STARTED:
        do_compile(package_name, path, logger)
    elif status == PackageStatus.EXIT_EARLY:
        logger.info(f"{package_name} exited early, remove and recompile")
        shutil.rmtree(os.path.join(path, package_name))
        logger.info(f"{package_name} remove ok")
        do_compile(package_name, path, logger)
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
        try:
            compile_package(package_name, path, logger)
        except Exception as e:
            logger.error(f"{e}")

def compile_list_worker(queue, path, idx):
    logger = logging.getLogger(f"worker{idx}")
    logger.setLevel(logging.DEBUG)
    logger.info(f"Start worker {idx}")
    while True:
        try:
            package_name = queue.get()
        except multiprocessing.Queue.Empty:
            logger.info(f"Worker {idx} meet queue empty, sleep")
            time.sleep(2)
        logger.info(f"Worker {idx} fetching package {package_name}, begin compile")
        compile_package(package_name, path, logger)

def compile_list_parallel(json_path, path, max_worker=10):
    logger = logging.getLogger(__file__)
    logger.setLevel(logging.DEBUG)
    logger.info(f"PARALLEL MODE, max_worker={max_worker}")
    logger.info("Start compiling list")
    logger.info("Reading compile list")
    with open(json_path) as f:
        package_list = json.load(f)
    logger.debug(f"{len(package_list)} packages to compile")
    manager = multiprocessing.Manager()
    queue = manager.Queue(max_worker * 5)
    pool = multiprocessing.Pool(max_worker)
    for idx in range(max_worker):
        pool.apply_async(compile_list_worker, (queue, path, idx))
    
    wait_count = 0
    for package in package_list:
        package_name = package['package']
        while True:
            qsize = queue.qsize()
            if qsize > max_worker * 2:
                if wait_count < 10:
                    time.sleep(0.1)
                    wait_count += 1
                else:
                    time.sleep(10)
            else:
                wait_count = 0
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
        if container.image.tags[0] == IMAGE:
            print(f"Removing container {container.id}")
            container.remove(force=True)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Docker driver for compile different packages")
    parser.add_argument("--package_list", type=str, required=True, help="""Path to package list json file
                        Content:
                        [
                            {
                                "package": PACKAGE_NAME(str),
                                "version": VERSION(str),
                                "description": DESCRIPTION(str)
                            },
                            ...
                        ]""")
    parser.add_argument("--output_path", type=str, required=True, help="Path to save compiled package")
    parser.add_argument("--log_path", type=str, help="Path to save compile log, if not provided, will use stdout/stderr")
    parser.add_argument("--parallel", type=int, default=1, help="Number of parallel compile, default 1") 
    args = parser.parse_args()
    if args.log_path is None:
        logging.basicConfig(log_level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename=args.log_path)
    
    if args.parallel == 1:
        compile_list_serially(args.package_list, args.output_path)
    else:
        compile_list_parallel(args.package_list, args.output_path, max_worker=args.parallel)