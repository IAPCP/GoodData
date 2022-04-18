#!/usr/bin/env python3

import docker

def remove_by_image(image_name):
    client = docker.from_env()
    for container in client.containers.list(all=True):
        if container.image.tags[0].split(':')[0] == image_name:
            print(container.id)
            container.remove(force=True)

if __name__ == '__main__':
    import sys
    remove_by_image(sys.argv[1])