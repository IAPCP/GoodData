from node import *
from py2neo import *
import typing
import sqlite3
from tqdm.auto import tqdm


def create_node(graph: Graph, package: Package, project_root: str, file_url: str) -> Node:
    if not os.path.exists(os.path.join(project_root, file_url)):
        raise Exception(
            f"Path {os.path.join(project_root, file_url)} does not exist")
    url = Url(file_url)
    file_path = os.path.join(project_root, file_url)
    file_info = magic.from_file(os.path.join(project_root, file_url))

    node = None
    # Switch on file type
    if file_info.startswith("C source"):
        node = Source(file_path, "C")
    elif file_info.startswith("C++ source"):
        node = Source(file_path, "C++")
    elif file_info.startswith("ELF 64-bit LSB relocatable"):
        node = Relocatable(file_path)
    elif file_info.startswith("ELF 64-bit LSB executable"):
        node = Executable(file_path)
    elif file_info.startswith("current ar archive"):
        node = ArchiveLib(file_path)
    elif file_info.startswith("ELF 64-bit LSB shared object"):
        node = SharedLib(file_path)
    elif file_info.startswith("ASCII text"):
        guess_type = get_lexer_for_filename(file_path).name
        if guess_type == "C":
            node = Source(file_path, "C")
        elif guess_type == "C++":
            node = Source(file_path, "C++")
        else:
            pass
    elif file_info == "very short file (no magic)":
        node = Dummy(file_path)
    else:
        pass
    if node is None:
        raise NodeTypeNotImplemented(
            f"File type not supported, magic info: \"{file_info}\", path: \"{file_url}\"")
    node_match = node.__class__.match(graph, node.hash)
    if node_match.count() == 1:
        node = node_match.first()
    elif node_match.count() > 1:
        raise Exception("Hash collision")
    else:
        pass
    node.package.add(package)
    node.url.add(url)
    graph.push(node)
    return node


def analyze_package(graph: Graph, project_root: str, package_name: str, optimization_level: str, dirname: str):
    package_url = os.path.join(
        "packages", dirname)
    gcc_url = os.path.join(package_url, "gcc")
    ld_url = os.path.join(package_url, "ld")
    gcc_task_name_list = os.listdir(os.path.join(project_root, gcc_url))
    ld_task_name_list = os.listdir(os.path.join(project_root, ld_url))
    package_node = Package(dirname, package_name, optimization_level)
    graph.push(package_node)
    for task_name in tqdm(gcc_task_name_list):
        task_url = os.path.join(gcc_url, task_name)
        input_node_list = []
        if os.path.exists(os.path.join(project_root, task_url, "input")):
            for input_object_name in os.listdir(os.path.join(project_root, task_url, "input")):
                input_object_url = os.path.join(
                    task_url, "input", input_object_name)
                input_object_node = create_node(
                    graph, package_node, project_root, input_object_url)
                input_node_list.append(input_object_node)
        output_node_list = []
        if os.path.exists(os.path.join(project_root, task_url, "output")):
            for output_object_name in os.listdir(os.path.join(project_root, task_url, "output")):
                output_object_url = os.path.join(
                    task_url, "output", output_object_name)
                output_object_node = create_node(
                    graph, package_node, project_root, output_object_url)
                output_node_list.append(output_object_node)
        for input_node in input_node_list:
            for output_node in output_node_list:
                if isinstance(output_node, Relocatable):
                    graph.create(Relationship(input_node.__node__,
                                 "GCC_C", output_node.__node__))
                else:
                    graph.create(Relationship(input_node.__node__,
                                 "GCC", output_node.__node__))
    for task_name in tqdm(ld_task_name_list):
        task_url = os.path.join(ld_url, task_name)
        input_node_list = []
        if os.path.exists(os.path.join(project_root, task_url, "input")):
            for input_object_name in os.listdir(os.path.join(project_root, task_url, "input")):
                input_object_url = os.path.join(
                    task_url, "input", input_object_name)
                input_object_node = create_node(
                    graph, package_node, project_root, input_object_url)
                input_node_list.append(input_object_node)
        output_node_list = []
        if os.path.exists(os.path.join(project_root, task_url, "output")):
            for output_object_name in os.listdir(os.path.join(project_root, task_url, "output")):
                output_object_url = os.path.join(
                    task_url, "output", output_object_name)
                output_object_node = create_node(
                    graph, package_node, project_root, output_object_url)
                output_node_list.append(output_object_node)
        for input_node in input_node_list:
            for output_node in output_node_list:
                graph.create(Relationship(input_node.__node__,
                             "LD", output_node.__node__))


def analyze_project(graph: Graph, project_root: str):
    db_path = os.path.join(project_root, "project_db.sqlite3")
    db_conn = sqlite3.connect(db_path)
    cursor = db_conn.execute("SELECT id, package_name, optimization_level, dirname FROM packages WHERE status = 'DONE'")
    for pid, package_name, optimization_level, dirname in cursor:
        print(f"Analyzing package {package_name}...")
        analyze_package(graph, project_root, package_name,
                        optimization_level, dirname)
        db_conn.execute("UPDATE packages SET status = 'ANALYZED' WHERE id = ?", (pid,))


if __name__ == '__main__':
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "test"))
    # analyze_package(graph, "/home/kjdy/projects/gd_small", "libnss-sss", "O2",
                    # "libnss-sss_O2_f31ca2af4cf242099e9efd6de10aeb0a")
    analyze_project(graph, "/home/kjdy/projects/gd_small")
