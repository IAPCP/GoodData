import atexit
import logging
import os
import shutil
import sqlite3
import threading
import docker
import time

IMAGE="compile_docker:latest"

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
            cursor.execute("CREATE TABLE packages (id INTEGER PRIMARY KEY AUTOINCREMENT, package_name TEXT, status TEXT)")
            for package_name in package_list:
                cursor.execute("INSERT INTO packages (package_name, status) VALUES (?, ?)", (package_name, "NOT_STARTED"))
            self.db_conn.commit()
        else:
            self.db_conn = sqlite3.connect(self.project_db_path)
        
        # Reset STARTED packages to NOT_STARTED
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT package_name FROM packages WHERE status = ?", ("STARTED",))
        res = cursor.fetchall()
        for package_name_tuple in res:
            package_name = package_name_tuple[0]
            self.logger.info("Resetting package %s to NOT_STARTED, removing the directory", package_name)
            os.system(f"sudo rm -rf {os.path.join(self.packages_root, package_name)}")
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
        
    def get_package_status(self, package_name):
        # NOT_FOUND, NOT_STARTED, STARTED, DONE, COMPILE_ERROR, PYTHON_ERROR
        res = self.db_exec(
            "SELECT status FROM packages WHERE package_name = ?", 
            (package_name,)
        )
        if len(res) == 0:
            status = "NOT_FOUND"
        else:
            if len(res) > 1:
                self.logger.error("Multiple entries for package name: %s", package_name)
            status = res[0][0]
        return status
    
    def set_package_status(self, package_name, status):
        if status not in ("NOT_STARTED", "STARTED", "DONE", "COMPILE_ERROR", "PYTHON_ERROR"):
            self.logger.error("Invalid status: %s", status)
            raise Exception("Invalid status")
        self.db_exec(
            "UPDATE packages SET status = ? WHERE package_name = ?", 
            (status, package_name)
        )
    
    def compile_package(self, package_name, optimization_level):
        if not optimization_level in ("0", "1", "2", "3", "g", "s", "fast"):
            self.logger.error("Invalid optimization level: %s", optimization_level)
            raise Exception("Invalid optimization level")
        self.logger.info("Compiling package %s", package_name)
        try:
            os.system(f"mkdir -p {os.path.join(self.packages_root, package_name)}")
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
                    os.path.abspath(os.path.join(self.packages_root, package_name)): {
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
            with open(os.path.join(self.packages_root, package_name, "python_error"), "w") as f:
                f.write(e.__str__())
            return "PYTHON_ERROR"
        if os.path.exists(os.path.join(self.packages_root, package_name, "compile_succeed")):
            self.logger.info(f"Package {package_name} compile succeed")
            return "DONE"
        else:
            return "COMPILE_ERROR"
        
    def compile_package_with_retry(self, package_name, optimization_level, retry):
        status = None
        tried = 0
        self.set_package_status(package_name, "STARTED")
        while True:
            status = self.compile_package(package_name, optimization_level)
            if status == "DONE" or status == "PYTHON_ERROR" or status == "STARTED":
                break
            elif status == "COMPILE_ERROR":
                if tried >= retry:
                    break
                self.logger.info(f"{package_name} compile error, retrying {tried + 1}/{retry}")
                os.system(f"sudo rm -rf {os.path.join(self.packages_root, package_name)}")
                tried += 1
            else:
                raise Exception("Invalid status")
        self.set_package_status(package_name, status)
        return status
    
    def get_packages_not_started(self, num_packages, set_started=True):
        if set_started:
            res = self.db_exec(
                "UPDATE packages SET status = ? WHERE package_name IN (SELECT package_name FROM packages WHERE status = ? LIMIT ?) RETURNING package_name",
                ("STARTED", "NOT_STARTED", num_packages)
            )
        else:
            res = self.db_exec(
                "SELECT package_name FROM packages WHERE status = ? LIMIT ?",
                ("NOT_STARTED", num_packages)
            )
        return [package[0] for package in res]
    
def compile_packages(compile_project, optimization_level, retry):
    while True:
        packages = compile_project.get_packages_not_started(1)
        if len(packages) == 0:
            break
        status = compile_project.compile_package_with_retry(packages[0], optimization_level, retry)
    
def compile_packages_parallel(compile_project, optimization_level, retry, max_parallel):
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
            target=compile_project.compile_package_with_retry, 
            args=(package, optimization_level, retry)
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
    with open("packages", "r") as f:
        import json
        package_list = json.load(f)
    packages = []
    for package in package_list:
        packages.append(package["package"])
    import sys
    project = CompileProject(sys.argv[1], packages)
    compile_packages_parallel(project, "0", 3, 40)
    