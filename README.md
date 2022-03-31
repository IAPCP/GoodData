# compile_docker集成gcc_parser和ld_hoo

Dockerfile里面有我的私人token（有效期90天），用于访问IAPCP的private仓库，因此Dockerfile不要外传；

由于可以访问私有仓库，因此可以直接build

```dockerfile
docker build -t hook_build -f Dockerfile .
```

## 测试样例
### LLVM编译
```bash
cd root
mkdir llvm
cd llvm
wget https://github.com/llvm/llvm-project/releases/download/llvmorg-13.0.0/llvm-project-13.0.0.src.tar.xz
tar xf llvm-project-13.0.0.src.tar.xz
mv llvm-project-13.0.0.src llvm-src
mkdir llvm-build
cd llvm-build

# cmake LLVM
cmake -G "Ninja" \
-DLLVM_ENABLE_PROJECTS="clang;clang-tools-extra;lldb;compiler-rt;lld" \
-DLLVM_ENABLE_RUNTIMES="libcxx;libcxxabi" \
-DCMAKE_BUILD_TYPE=Release \
-DLLVM_TARGETS_TO_BUILD="X86" \
-DCMAKE_CXX_FLAGS="-std=c++11" \
../llvm-src/llvm/

# compile
COMPILE_COMMANDS_DB=/root/llvm/llvm.db PROJ_ROOT=/root/llvm/llvm-build ninja
```
会生成一个600M+的数据库文件