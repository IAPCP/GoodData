from node import *
from py2neo import *
import typing
from tqdm.auto import tqdm


def analyze_package(graph: Graph, project_root: str, package_name: str, optimization_level: str, uuid: str):
    package_url = os.path.join("packages", package_name + "_" + optimization_level + "_" + uuid)
    gcc_url = os.path.join(package_url, "gcc")
    ld_url = os.path.join(package_url, "ld")
    gcc_task_name_list = os.listdir(os.path.join(project_root, gcc_url))
    ld_task_name_list = os.listdir(os.path.join(project_root, ld_url))
    package_node = Package(uuid, package_name, optimization_level)
    graph.push(package_node)
    for task_name in tqdm(gcc_task_name_list):
        task_url = os.path.join(gcc_url, task_name)
        input_node_list = []
        if os.path.exists(os.path.join(project_root, task_url, "input")):
            for input_object_name in os.listdir(os.path.join(project_root, task_url, "input")):
                input_object_url = os.path.join(task_url, "input", input_object_name)
                input_object_node = create_node(graph, project_root, input_object_url)
                graph.create(Relationship(input_object_node.__node__, "BELONGS_TO", package_node.__node__))
                input_node_list.append(input_object_node)
        output_node_list = []
        if os.path.exists(os.path.join(project_root, task_url, "output")):
            for output_object_name in os.listdir(os.path.join(project_root, task_url, "output")):
                output_object_url = os.path.join(task_url, "output", output_object_name)
                output_object_node = create_node(graph, project_root, output_object_url)
                graph.create(Relationship(output_object_node.__node__, "BELONGS_TO", package_node.__node__))
                output_node_list.append(output_object_node)
        for input_node in input_node_list:
            for output_node in output_node_list:
                graph.create(Relationship(input_node.__node__, "GCC", output_node.__node__))
    for task_name in tqdm(ld_task_name_list):
        task_url = os.path.join(ld_url, task_name)
        input_node_list = []
        if os.path.exists(os.path.join(project_root, task_url, "input")):
            for input_object_name in os.listdir(os.path.join(project_root, task_url, "input")):
                input_object_url = os.path.join(task_url, "input", input_object_name)
                input_object_node = create_node(graph, project_root, input_object_url)
                graph.create(Relationship(input_object_node.__node__, "BELONGS_TO", package_node.__node__))
                input_node_list.append(input_object_node)
        output_node_list = []
        if os.path.exists(os.path.join(project_root, task_url, "output")):
            for output_object_name in os.listdir(os.path.join(project_root, task_url, "output")):
                output_object_url = os.path.join(task_url, "output", output_object_name)
                output_object_node = create_node(graph, project_root, output_object_url)
                graph.create(Relationship(output_object_node.__node__, "BELONGS_TO", package_node.__node__))
                output_node_list.append(output_object_node)
        for input_node in input_node_list:
            for output_node in output_node_list:
                graph.create(Relationship(input_node.__node__, "LD", output_node.__node__))
        

if __name__ == '__main__':
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "test"))
    analyze_package(graph, "/home/kjdy/projects/gd_small", "libnss-sss", "O2", "f31ca2af4cf242099e9efd6de10aeb0a")
