import atexit
import logging
import os
import shutil
import sqlite3
import threading
import docker
import time
import uuid

IMAGE="compile_docker:latest"

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
        
        # Reset STARTED packages to NOT_STARTED
        cursor = self.db_conn.cursor()
        cursor.execute(
            "SELECT package_name, optimization_level, dirname FROM packages WHERE status = ?", 
            ("STARTED",)
        )
        res = cursor.fetchall()
        for package_name, optimization_level, dirname in res:
            self.logger.info("Resetting package %s of O%s to NOT_STARTED, removing the directory %s", package_name, optimization_level, dirname)
            os.system(f"sudo rm -rf {os.path.join(self.packages_root, dirname)}")
        cursor.execute("UPDATE packages SET status = ? WHERE status = ?", ("NOT_STARTED", "STARTED"))
        self.db_conn.commit()
    
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
    
    def compile_package_internal(self, package_name, optimization_level, dirname):
        if not optimization_level in ("0", "1", "2", "3", "g", "s", "fast"):
            self.logger.error("Invalid optimization level: %s", optimization_level)
            raise Exception("Invalid optimization level")
        save_path = os.path.join(self.packages_root, dirname)
        self.logger.info("Compiling package %s with optimization_level -O%s in %s", package_name, optimization_level, save_path)
        try:
            os.system(f"mkdir -p {save_path}")
            client = docker.from_env()
            result = client.containers.run(
                image=IMAGE,
                command=[
                    "/bin/sh", 
                    "-c", 
                    f"/root/compile.sh {package_name} {optimization_level} 2>&1 > /root/package/output.log || chown -R {os.getgid()}:{os.getuid()} /root/package"
                ],
                remove=True,
                volumes={
                    os.path.abspath(save_path): {
                        "bind": "/root/package",
                        "mode": "rw"
                    }
                }
            )
        except docker.errors.APIError:
            return "STARTED"
        except Exception as e:
            self.logger.error("Python error compiling package %s", package_name)
            self.logger.error(f"Error: {e}")
            import traceback
            self.logger.error(f"Trace: {traceback.format_exc()}")
            with open(os.path.join(save_path, "python_error"), "w") as f:
                f.write(e.__str__())
            return "PYTHON_ERROR"
        if os.path.exists(os.path.join(save_path, "compile_succeed")):
            self.logger.info(f"Package {package_name} compile succeed")
            return "DONE"
        else:
            return "COMPILE_ERROR"
        
    def compile_package(self, package_id, package_name, optimization_level, dirname, retry):
        status = None
        tried = 0
        self.set_package_status(package_id , "STARTED")
        while True:
            status = self.compile_package_internal(package_name, optimization_level, dirname)
            if status == "DONE" or status == "PYTHON_ERROR" or status == "STARTED":
                break
            elif status == "COMPILE_ERROR":
                if tried >= retry:
                    break
                self.logger.info(f"{package_name} with optimization_level O{optimization_level} compile error, retrying {tried + 1}/{retry}")
                os.system(f"sudo rm -rf {dirname}")
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
    
def compile_packages(compile_project: CompileProject, retry: int):
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
            retry
        )
    
def compile_packages_parallel(compile_project: CompileProject, retry: int, max_parallel: int):
    import threading
    thread_list = []
    while True:
        for thread in thread_list:
            if not thread.is_alive():
                thread.join()
                thread_list.remove(thread)
        if len(thread_list) >= max_parallel:
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
                retry
            )
        )
        thread.daemon = True
        thread.start()
        thread_list.append(thread)


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

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    with open("packages.json", "r") as f:
        import json
        package_list = json.load(f)
    packages = []
    for package in package_list:
        packages.append(package["package"])
    import sys
    project = CompileProject(sys.argv[1], packages)
    compile_packages_parallel(project, 3, 4)
    