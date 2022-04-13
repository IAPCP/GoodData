#!/usr/bin/env python3

# get content from url
def get_url(url):
    import urllib.request
    return urllib.request.urlopen(url).read()

# extract content of a gzip file string
def extract_gzip(data):
    import gzip
    return gzip.decompress(data).decode('utf-8')

def extract_line(line):
    for idx in range(len(line)):
        if line[idx] == '(':
            left = idx
        if line[idx] == ')':
            right = idx
            break
    return line[:left].strip(), line[left + 1: right].strip(), line[right + 1: ].strip()

def extract_package(data):
    lines = data.split('\n')
    packages = []
    for line in lines:
        if '(' in line and ')' in line:
            package, version, description = extract_line(line)
            packages.append({'package': package, 'version': version, 'description': description})
    return packages


if __name__ == '__main__':
    data = get_url("https://packages.ubuntu.com/focal/allpackages?format=txt.gz")
    data = extract_gzip(data)
    import pprint
    pprint.pprint(extract_package(data))
