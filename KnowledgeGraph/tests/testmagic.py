#!/usr/bin/env python3
import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from nodes import *


def traverse_package(project_root: str, package_name: str, driver: neo4j.Driver):
    for gcc_task in os.listdir(os.path.join(project_root, "packages", package_name, "gcc")):
        task_path = os.path.join("packages", package_name, "gcc", gcc_task)
        if os.path.exists(os.path.join(project_root, task_path, "input")):
            input_files = os.listdir(os.path.join(
                project_root, task_path, "input"))
            for input_file in input_files:
                create_node(project_root, os.path.join(task_path, "input",
                            input_file)).update_database(driver)
        if os.path.exists(os.path.join(project_root, task_path, "output")):
            output_files = os.listdir(os.path.join(
                project_root, task_path, "output"))
            for output_file in output_files:
                create_node(project_root, os.path.join(task_path, "output",
                            output_file)).update_database(driver)
    for ld_task in os.listdir(os.path.join(project_root, "packages", package_name, "ld")):
        task_path = os.path.join("packages", package_name, "ld", ld_task)
        if os.path.exists(os.path.join(project_root, task_path, "input")):
            input_files = os.listdir(os.path.join(
                project_root, task_path, "input"))
            for input_file in input_files:
                create_node(project_root, os.path.join(task_path, "input",
                            input_file)).update_database(driver)
        if os.path.exists(os.path.join(project_root, task_path, "output")):
            output_files = os.listdir(os.path.join(
                project_root, task_path, "output"))
            for output_file in output_files:
                create_node(project_root, os.path.join(task_path, "output",
                            output_file)).update_database(driver)


def traverse_project(project_root: str, driver: neo4j.Driver):
    for package_name in os.listdir(os.path.join(project_root, "packages")):
        traverse_package(project_root, package_name, driver)


if __name__ == '__main__':
    project_root = sys.argv[1]
    driver = neo4j.GraphDatabase.driver(
        "bolt://localhost:7687", auth=("neo4j", "test"))
    traverse_project(project_root, driver)
