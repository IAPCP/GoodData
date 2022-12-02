# GoodData
Compile Manager, gcc_parser and ld_hook integreted.

## SubModules
```bash
git clone --recursive git@github.com:IAPCP/GoodData.git
```
or
```bash
git clone git@github.com:IAPCP/GoodData.git
cd GoodData
git submodule init
```


## Prepare Docker
```bash
cd docker
docker build -t compile_docker -f Dockerfile .
```
Edit variable IMAGE in compile_project.py to the docker image's tag.

## Dependencies
### package
sqlite3 >= 3.35.0
docker

### python
psutil