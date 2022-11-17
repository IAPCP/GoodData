import os
import enum

PackageStatus = enum.Enum("PackageStatus", ("NOT_STARTED", "EXIT_EARLY", "DONE", "ERROR"))

def package_status(package_name, path):
    save_path = os.path.join(path, package_name)
    if not os.path.exists(save_path):
        return PackageStatus.NOT_STARTED
    if os.path.exists(os.path.join(save_path, "done")):
        return PackageStatus.DONE
    if os.path.exists(os.path.join(save_path, "error")):
        return PackageStatus.ERROR
    return PackageStatus.EXIT_EARLY

def package_use_gcc(package_name, path):
    save_path = os.path.join(path, package_name)
    return os.path.exists(os.path.join(save_path, "compile_commands.db"))
