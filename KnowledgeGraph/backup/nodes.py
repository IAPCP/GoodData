#!/usr/bin/env python3

import os
import hashlib
import neo4j
import magic
from pygments.lexers import get_lexer_for_filename


class NodeTypeNotImplemented(Exception):
    pass


class Node:
    def __init__(self, project_root: str, file_url: str):
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
        self.file_hash = calc_file_hash(os.path.join(project_root, file_url))
        self.file_url = file_url
        self.properties = {
            "file_name": os.path.basename(file_url)
        }

    @property
    def type(self) -> str:
        raise Exception("Not implemented")

    def _update_database(self, tx: neo4j.Transaction):
        if not self.type.isidentifier():
            raise Exception("Node type is not a valid identifier")
        tx.run(f"""MERGE (node: {self.type} {{file_hash: $file_hash}})
               SET node += $properties
               SET node.file_url = (CASE
                        WHEN node.file_url IS NULL THEN [$file_url]
                        ELSE (CASE
                                WHEN $file_url IN node.file_url THEN node.file_url
                                ELSE node.file_url + $file_url
                            END)
                   END)
               """,
               file_hash=self.file_hash,
               properties=self.properties,
               file_url=self.file_url)

    def update_database(self, driver: neo4j.Driver):
        with driver.session() as session:
            session.execute_write(self._update_database)


class SourceNode(Node):
    def __init__(self, project_root: str, file_url: str, language: str):
        super(SourceNode, self).__init__(project_root, file_url)
        file_magic_info = magic.from_file(
            os.path.join(project_root, file_url))
        self.properties["magic_info"] = file_magic_info
        self.properties["language"] = language

    @property
    def type(self) -> str:
        return "Source"


class RelocatableNode(Node):
    def __init__(self, project_root: str, file_url: str):
        super(RelocatableNode, self).__init__(project_root, file_url)
        file_magic_info = magic.from_file(
            os.path.join(project_root, file_url))
        self.properties["magic_info"] = file_magic_info

    @property
    def type(self) -> str:
        return "RelocObject"


class ExecutableNode(Node):
    def __init__(self, project_root: str, file_url: str):
        super(ExecutableNode, self).__init__(project_root, file_url)
        file_magic_info = magic.from_file(
            os.path.join(project_root, file_url))
        self.properties["magic_info"] = file_magic_info

    @ property
    def type(self) -> str:
        return "Executable"


class ArchiveLibNode(Node):
    def __init__(self, project_root: str, file_url: str):
        super(ArchiveLibNode, self).__init__(project_root, file_url)
        file_magic_info = magic.from_file(
            os.path.join(project_root, file_url))
        self.properties["magic_info"] = file_magic_info

    @ property
    def type(self) -> str:
        return "ArchiveLib"


class SharedLibNode(Node):
    def __init__(self, project_root: str, file_url: str):
        super(SharedLibNode, self).__init__(project_root, file_url)
        file_magic_info = magic.from_file(
            os.path.join(project_root, file_url))
        self.properties["magic_info"] = file_magic_info

    @ property
    def type(self) -> str:
        return "SharedLib"


class PackageNode(Node):
    def __init__(self, project_root: str, package_name: str):
        super(PackageNode, self).__init__(project_root,
                                          os.path.join("packages", package_name))
        self.properties["package_name"] = package_name

    @ property
    def type(self) -> str:
        return "Package"


class DummyNode(Node):
    def __init__(self, project_root: str, file_url: str):
        super(DummyNode, self).__init__(project_root, file_url)
        file_magic_info = magic.from_file(
            os.path.join(project_root, file_url))
        self.properties["magic_info"] = file_magic_info

    @ property
    def type(self) -> str:
        return "Dummy"


def create_node(project_root: str, file_url: str) -> Node:
    if not os.path.exists(os.path.join(project_root, file_url)):
        raise Exception(
            f"Path {os.path.join(project_root, file_url)} does not exist")
    file_info = magic.from_file(os.path.join(project_root, file_url))

    # Switch on file type
    if file_info.startswith("C source"):
        return SourceNode(project_root, file_url, "C")
    elif file_info.startswith("C++ source"):
        return SourceNode(project_root, file_url, "C++")
    elif file_info.startswith("ELF 64-bit LSB relocatable"):
        return RelocatableNode(project_root, file_url)
    elif file_info.startswith("ELF 64-bit LSB executable"):
        return ExecutableNode(project_root, file_url)
    elif file_info.startswith("current ar archive"):
        return ArchiveLibNode(project_root, file_url)
    elif file_info.startswith("ELF 64-bit LSB shared object"):
        return SharedLibNode(project_root, file_url)
    elif file_info.startswith("ASCII text"):
        guess_type = get_lexer_for_filename(
            os.path.join(project_root, file_url)).name
        if guess_type == "C":
            return SourceNode(project_root, file_url, "C")
        elif guess_type == "C++":
            return SourceNode(project_root, file_url, "C++")
        else:
            pass
    elif file_info == "very short file (no magic)":
        return DummyNode(project_root, file_url)
    else:
        pass
    raise NodeTypeNotImplemented(
        f"File type not supported, magic info: \"{file_info}\", path: \"{file_url}\"")


if __name__ == '__main__':
    import sys
    print(magic.from_file(sys.argv[1]))
    node = create_node(sys.argv[1])
    driver = neo4j.GraphDatabase.driver(
        "bolt://localhost:7687", auth=("neo4j", "test"))
    node.update_database(driver)
