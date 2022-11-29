#!/usr/bin/env python3

import os
import hashlib

def file_hash(file_path: str) -> str:
    """Returns the SHA256 hash of the file at the given path."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            sha256.update(data)    
    return sha256.hexdigest()



if __name__ == '__main__':
    h = file_hash('/bin/ls')
    print(type(h))