from py2neo import *
from py2neo.ogm import *
from pygments.lexers import get_lexer_for_filename

import magic
import os
import hashlib


class NodeTypeNotImplemented(Exception):
    pass


class KnowledgeGraphNode(Model):
    __primarykey__ = "hash"
    hash = Property()
    url = Property()
    magic_info = Property()

    def __init__(self, project_root: str, url: str):
        def calc_file_hash(target_file_path: str) -> str:
            """Returns the SHA256 hash of the file at the given path."""
            sha256 = hashlib.sha256()
            with open(target_file_path, 'rb') as f:
                while True:
                    data = f.read(65536)
                    if not data:
                        break
                    sha256.update(data)
            return sha256.hexdigest()
        super(KnowledgeGraphNode, self).__init__()
        self.hash = calc_file_hash(os.path.join(project_root, url))
        self.url = [url]
        self.magic_info = magic.from_file(os.path.join(project_root, url))


class Source(KnowledgeGraphNode):
    language = Property()

    def __init__(self, project_root: str, url: str, language: str):
        super(Source, self).__init__(project_root, url)
        self.language = language


class Relocatable(KnowledgeGraphNode):
    def __init__(self, project_root: str, url: str):
        super(Relocatable, self).__init__(project_root, url)


class Executable(KnowledgeGraphNode):
    def __init__(self, project_root: str, url: str):
        super(Executable, self).__init__(project_root, url)


class ArchiveLib(KnowledgeGraphNode):
    def __init__(self, project_root: str, url: str):
        super(ArchiveLib, self).__init__(project_root, url)


class SharedLib(KnowledgeGraphNode):
    def __init__(self, project_root: str, url: str):
        super(SharedLib, self).__init__(project_root, url)


class Dummy(KnowledgeGraphNode):
    def __init__(self, project_root: str, url: str):
        super(Dummy, self).__init__(project_root, url)


class Package(Model):
    __primarykey__ = "uuid"
    uuid = Property()
    package_name = Property()
    optimization_level = Property()

    def __init__(self, uuid: str, package_name: str, optimization_level: str):
        super(Package, self).__init__()
        self.uuid = uuid
        self.package_name = package_name
        self.optimization_level = optimization_level


def create_node(graph: Graph, project_root: str, file_url: str) -> Node:
    if not os.path.exists(os.path.join(project_root, file_url)):
        raise Exception(
            f"Path {os.path.join(project_root, file_url)} does not exist")
    file_info = magic.from_file(os.path.join(project_root, file_url))

    node = None
    # Switch on file type
    if file_info.startswith("C source"):
        node = Source(project_root, file_url, "C")
    elif file_info.startswith("C++ source"):
        node = Source(project_root, file_url, "C++")
    elif file_info.startswith("ELF 64-bit LSB relocatable"):
        node = Relocatable(project_root, file_url)
    elif file_info.startswith("ELF 64-bit LSB executable"):
        node = Executable(project_root, file_url)
    elif file_info.startswith("current ar archive"):
        node = ArchiveLib(project_root, file_url)
    elif file_info.startswith("ELF 64-bit LSB shared object"):
        node = SharedLib(project_root, file_url)
    elif file_info.startswith("ASCII text"):
        guess_type = get_lexer_for_filename(
            os.path.join(project_root, file_url)).name
        if guess_type == "C":
            node = Source(project_root, file_url, "C")
        elif guess_type == "C++":
            node = Source(project_root, file_url, "C++")
        else:
            pass
    elif file_info == "very short file (no magic)":
        node = Dummy(project_root, file_url)
    else:
        pass
    if node is None:
        raise NodeTypeNotImplemented(
            f"File type not supported, magic info: \"{file_info}\", path: \"{file_url}\"")
    tx = graph.begin()
    node_match = node.__class__.match(graph, node.hash)
    if node_match.count() == 0:
        tx.push(node)
        tx.commit()
    elif node_match.count() == 1:
        maybe_node = node_match.all()[0]
        node.url = list(set(node.url).union(set(maybe_node.url)))
        tx.push(node)
        graph.commit(tx)
    else:
        raise Exception("More than one node with the same hash")
    return node

if __name__ == '__main__':
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "test"))
    node1 = create_node(graph, "/home/kjdy/test/testob", "omg.c")
    node2 = create_node(graph, "/home/kjdy/test/testob", "test.c")
    import ipdb; ipdb.set_trace()
    
    
        