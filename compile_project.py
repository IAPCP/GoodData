#!/usr/bin/env python3
import atexit
import sys
import logging
import os
import shutil
import sqlite3
import threading
import docker
import time
import uuid
import psutil
import argparse
from tqdm.auto import tqdm

IMAGE="compile_docker:zbl"
SLOW_START_INTERVAL=30

def dir_name(package: str, optimization_level: str) -> str:
    return package + "_O" + optimization_level + "_" + uuid.uuid4().hex

class CompileProject:
    def __init__(self, project_root, package_list=None):
        self.project_root = project_root
        self.packages_root = os.path.join(project_root, "packages")
        self.project_db_path = os.path.join(project_root, "project_db.sqlite3")
        self.initialized = os.path.exists(self.project_db_path)
        self.logger = logging.getLogger("CompileProject")
        self.db_conn = None
    
        if not self.initialized:
            self.logger.info("Project database not found, creating new one")
            os.system(f"mkdir -p {self.packages_root}")
            if package_list is None:
                self.logger.error("Package list is required to create a new project database")
                raise Exception("Package list is required to create a new project database")
            self.db_conn = sqlite3.connect(self.project_db_path)
            cursor = self.db_conn.cursor()
            cursor.execute("CREATE TABLE packages (id INTEGER PRIMARY KEY AUTOINCREMENT, package_name TEXT, optimization_level TEXT, status TEXT, dirname TEXT)")
            for package_name in package_list:
                for optimization_level in ("0", "1", "2", "3", "g", "s", "fast"):
                    cursor.execute(
                        "INSERT INTO packages (package_name, optimization_level, status, dirname) VALUES (?, ?, ?, ?)", 
                        (package_name, optimization_level, "NOT_STARTED", dir_name(package_name, optimization_level))
                    )
            self.db_conn.commit()
        else:
            self.db_conn = sqlite3.connect(self.project_db_path)
    
    def db_exec(self, *args):
        db_conn = None
        while True:
            try:
                db_conn = sqlite3.connect(self.project_db_path)
                break
            except sqlite3.Error as e:
                self.logger.error("Error connecting to database: %s", e)
                continue
        res = db_conn.execute(*args).fetchall()
        db_conn.commit()
        db_conn.close()
        return res
    
    def consolidate(self, strict=False):
        # Check directories
        self.logger.info("Consolidate.")
        res = self.db_exec(
            "SELECT id, dirname, status FROM packages"
        )
        for _id, dirname, status in tqdm(res):
            if strict:
                need_restore = (status != "DONE" and os.path.exists(os.path.join(self.packages_root, dirname)))
            else:
                need_restore = (status == "STARTED")
            
            if need_restore:
                self.logger.info("Directory %s already exists, delete it", dirname)
                os.system(f"rm -rf {os.path.join(self.packages_root, dirname)}")
                self.set_package_status(_id, "NOT_STARTED")
            
        
    def get_package_status(self, package_id: int) -> str:
        # NOT_FOUND, NOT_STARTED, STARTED, DONE, COMPILE_ERROR, PYTHON_ERROR
        res = self.db_exec(
            "SELECT status FROM packages WHERE id = ?", 
            (package_id,)
        )
        if len(res) == 0:
            status = "NOT_FOUND"
        else:
            status = res[0][0]
        return status
    
    def set_package_status(self, package_id, status):
        if status not in ("NOT_STARTED", "STARTED", "DONE", "COMPILE_ERROR", "PYTHON_ERROR"):
            self.logger.error("Invalid status: %s", status)
            raise Exception("Invalid status")
        self.db_exec(
            "UPDATE packages SET status = ? WHERE id = ?", 
            (status, package_id)
        )
    
    def compile_package_internal(self, package_name, optimization_level, dirname, in_memory=False):
        if not optimization_level in ("0", "1", "2", "3", "g", "s", "fast"):
            self.logger.error("Invalid optimization level: %s", optimization_level)
            raise Exception("Invalid optimization level")
        save_path = os.path.join(self.packages_root, dirname)
        self.logger.info("Compiling package %s with optimization_level -O%s in %s", package_name, optimization_level, save_path)
        try:
            os.system(f"mkdir -p {save_path}")
            # Prepare command string
            command_str = f"compile.sh {package_name} {os.getuid()} {os.getgid()}"
            
            # Prepare environments
            environments = {
                "GCC_PARSER_HIJACK_OPTIMIZATION_LEVEL": optimization_level,
                "GCC_PARSER_HIJACK_DWARF4": "1"
            }
            
            if in_memory:
                client = docker.from_env()
                result = client.containers.run(
                    image=IMAGE,
                    command=[
                        "/bin/sh",
                        "-c",
                        command_str
                    ],
                    remove=True,
                    environment=environments,
                    volumes={
                        os.path.abspath(save_path): {
                            "bind": "/save",
                            "mode": "rw"
                        }
                    },
                    tmpfs={
                        "/workspace": "exec"
                    },
                    name=f"{package_name}_O{optimization_level}"
                )
            else:
                # Prepare environments
                environments["SAVE_PATH"] = "/workspace/package"
                
                client = docker.from_env()
                result = client.containers.run(
                    image=IMAGE,
                    command=[
                        "/bin/sh", 
                        "-c", 
                        command_str
                    ],
                    remove=True,
                    environment=environments,
                    volumes={
                        os.path.abspath(save_path): {
                            "bind": "/workspace/package",
                            "mode": "rw"
                        }
                    },
                    name=f"{package_name}_O{optimization_level}"
                )
        except docker.errors.APIError:
            return "STARTED"
        except Exception as e:
            self.logger.error(f"Python error compiling package {package_name} with optimization_level -O{optimization_level}")
            self.logger.error(f"Error: {e}")
            import traceback
            self.logger.error(f"Trace: {traceback.format_exc()}")
            with open(os.path.join(save_path, "python_error"), "w") as f:
                f.write(e.__str__())
            return "PYTHON_ERROR"
        if os.path.exists(os.path.join(save_path, "compile_succeed")):
            self.logger.info(f"Package {package_name} with optimization_level -O{optimization_level} compile succeed")
            return "DONE"
        else:
            return "COMPILE_ERROR"
        
    def compile_package(self, package_id, package_name, optimization_level, dirname, retry, in_memory):
        status = None
        tried = 0
        self.set_package_status(package_id , "STARTED")
        while True:
            status = self.compile_package_internal(package_name, optimization_level, dirname, in_memory)
            if status == "DONE" or status == "PYTHON_ERROR" or status == "STARTED":
                break
            elif status == "COMPILE_ERROR":
                if tried >= retry:
                    break
                self.logger.info(f"{package_name} with optimization_level O{optimization_level} compile error, retrying {tried + 1}/{retry}")
                os.system(f"rm -rf {dirname}")
                tried += 1
            else:
                raise Exception("Invalid status")
        self.set_package_status(package_id, status)
        return status
    
    def get_packages_not_started(self, num_packages, set_started=True):
        if set_started:
            res = self.db_exec(
                "UPDATE packages SET status = ? WHERE id IN (SELECT id FROM packages WHERE status = ? LIMIT ?) RETURNING id, package_name, optimization_level, dirname",
                ("STARTED", "NOT_STARTED", num_packages)
            )
        else:
            res = self.db_exec(
                "SELECT id, package_name, optimization_level, dirname FROM packages WHERE status = ? LIMIT ?",
                ("NOT_STARTED", num_packages)
            )
        to_ret = []
        for item in res:
            to_ret.append({
                "package_id": item[0],
                "package_name": item[1],
                "optimization_level": item[2],
                "dirname": item[3]
            })
        return to_ret
    
def compile_packages(compile_project: CompileProject, retry: int, in_memory: bool):
    while True:
        packages = compile_project.get_packages_not_started(1)
        if len(packages) == 0:
            break
        package = packages[0]
        status = compile_project.compile_package(
            package["package_id"],
            package["package_name"],
            package["optimization_level"],
            package["dirname"],
            retry,
            in_memory
        )
    
def compile_packages_parallel(compile_project: CompileProject, retry: int, max_parallel: int, in_memory: bool):
    import threading
    thread_list = []
    slow_start_count = 0
    while True:
        for thread in thread_list:
            if not thread.is_alive():
                thread.join()
                thread_list.remove(thread)
        if len(thread_list) >= max_parallel or psutil.cpu_percent() >= 80:
            time.sleep(1)
            continue
        packages = compile_project.get_packages_not_started(1)
        if len(packages) == 0:
            break
        package = packages[0]
        thread = threading.Thread(
            target=compile_project.compile_package, 
            args=(
                package["package_id"],
                package["package_name"],
                package["optimization_level"],
                package["dirname"],
                retry,
                in_memory
            )
        )
        thread.daemon = True
        thread.start()
        thread_list.append(thread)
        if slow_start_count <= max_parallel:
            print(f"Slow start {slow_start_count}/{max_parallel}, waiting for {SLOW_START_INTERVAL} seconds")
            time.sleep(SLOW_START_INTERVAL)
            slow_start_count += 1


@atexit.register    
def clean_container():
    if not threading.current_thread().name == 'MainThread':
        return 
    print("Cleaning container")
    client = docker.from_env()
    for container in client.containers.list(all=True):
        if container.image.tags[0] == IMAGE:
            print(f"Removing container {container.id}")
            try:
                container.remove(force=True)
            except Exception:
                print(f"Failed to remove container {container.id}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--retry", type=int, default=3, help="Retry times when 'compile_error' occurs")
    parser.add_argument("-j", "--parallel", type=int, default=1, help="Max parallel jobs")
    parser.add_argument("-p", "--project", type=str, required=True, help="Project path")
    parser.add_argument("-l", "--list", type=str, required=True, help="List of packages to compile, must be a json file")
    parser.add_argument("-M", "--in-memory", action="store_true", help="Determines whether to use ramdisk to accelerate compilation")
    parser.add_argument("-S", "--strict", action="store_true", help="Determines whether consolidate use strict mode, if set, PYTHON_ERROR may be restored")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    with open(args.list, "r") as f:
        import json
        package_list = json.load(f)
    project = CompileProject(args.project, package_list)
    project.consolidate(args.strict)
    compile_packages_parallel(project, args.retry, args.parallel, args.in_memory)

def test():
    logging.basicConfig(level=logging.INFO)
    packages = [
        "nginx",
        "tree",
        "sl"
    ]
    project = CompileProject(sys.argv[1], packages)
    project.consolidate()
    compile_packages(project, 3, True)

if __name__ == '__main__':
    main()
    # test()
    
