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


## Dependencies
### package
sqlite3 >= 3.35.0
docker

### python
psutil

## Usage: 

 1. __prepare the docker__: following the steps above with the target of building the image.

 2. __Edit variable IMAGE__ in compile_project.py to the docker image's tag.

 3. Execute the following command to create the pakcages' list:

    ```
    python3 ./get_all_packages.py all_package.json
    ```

    This command stores the information of all packages in all_package.json

 4. Make a new folder for the results of compilation:

    ```
     mkdir compilation_folder
    ```

5. Start to compile:

   ```
   python3 compile_project.py  -l ./all_package.json -p ./compilation_folder
   ```

   

