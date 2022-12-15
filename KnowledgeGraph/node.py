from py2neo import *
from py2neo.ogm import *
from pygments.lexers import get_lexer_for_filename

import magic
import os
import hashlib


class NodeTypeNotImplemented(Exception):
    pass


class Package(Model):
    __primarykey__ = "dirname"
    package_name = Property()
    optimization_level = Property()
    dirname = Property()

    def __init__(self, dirname: str, package_name: str, optimization_level: str):
        super(Package, self).__init__()
        self.package_name = package_name
        self.optimization_level = optimization_level
        self.dirname = dirname


class Url(Model):
    __primarykey__ = "path"
    path = Property()

    def __init__(self, path: str):
        super(Url, self).__init__()
        self.path = path


class KnowledgeGraphNode(Model):
    __primarykey__ = "hash"
    name = Property()
    hash = Property()
    magic_info = Property()
    url = RelatedTo(Url, "LocatedAt")
    package = RelatedTo(Package, "BelongsTo")

    def __init__(self, path: str):
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
        self.hash = calc_file_hash(path)
        self.magic_info = magic.from_file(path)
        self.name = os.path.basename(path)


class Source(KnowledgeGraphNode):
    language = Property()

    def __init__(self, path: str, language: str):
        super(Source, self).__init__(path)
        self.language = language


class Relocatable(KnowledgeGraphNode):
    def __init__(self, path: str):
        super(Relocatable, self).__init__(path)


class Executable(KnowledgeGraphNode):
    def __init__(self, path: str):
        super(Executable, self).__init__(path)


class ArchiveLib(KnowledgeGraphNode):
    def __init__(self, path: str):
        super(ArchiveLib, self).__init__(path)


class SharedLib(KnowledgeGraphNode):
    def __init__(self, path: str):
        super(SharedLib, self).__init__(path)


class Dummy(KnowledgeGraphNode):
    def __init__(self, path: str):
        super(Dummy, self).__init__(path)
