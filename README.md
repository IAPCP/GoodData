# compile_docker集成gcc_parser和ld_hoo

Dockerfile里面有我的私人token（有效期90天），用于访问IAPCP的private仓库，因此Dockerfile不要外传；

由于可以访问私有仓库，因此可以直接build

```dockerfile
docker build -t hook_build -f Dockerfile .
```