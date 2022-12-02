FROM ubuntu:20.04

COPY sources.list /etc/apt/sources.list

RUN DEBIAN_FRONTEND=noninteractive apt -y update && \
        DEBIAN_FRONTEND=noninteractive apt -y upgrade && \
        DEBIAN_FRONTEND=noninteractive apt -y install build-essential curl git wget libgmp-dev libmpfr-dev libmpc-dev python3-pip ninja-build cmake bison flex texinfo dpkg-dev devscripts

RUN cd /root && \
        mkdir -p ld_hook/build && \
        mkdir -p gcc_parser/build

COPY gcc_parser /root/gcc_parser/gcc_parser
COPY ld_hook /root/ld_hook/ld_hook

RUN cd /root/ld_hook/build && \
        ../ld_hook/configure --prefix=/usr && \
        make -j${nproc} && \
        make install

# prepare gcc_parser
RUN cd /root/gcc_parser/build && \
        pip3 install robotpy-cppheaderparser psutil && \
        ../gcc_parser/configure --prefix=/usr -enable-language=c,c++ --disable-multilib --disable-werror --disable-bootstrap && \
        make -j${nproc} && \
        make install

RUN rm /usr/lib/x86_64-linux-gnu/libstdc++.so.6 && \
        ln -s /usr/lib64/libstdc++.so.6 /usr/lib/x86_64-linux-gnu/libstdc++.so.6 && \
        rm /usr/bin/x86_64-linux-gnu-gcc && \
        ln -s gcc /usr/bin/x86_64-linux-gnu-gcc && \
        rm /usr/bin/x86_64-linux-gnu-gcc-ar && \
        ln -s gcc-ar /usr/bin/x86_64-linux-gnu-gcc-ar && \
        rm /usr/bin/x86_64-linux-gnu-gcc-nm && \
        ln -s gcc-nm /usr/bin/x86_64-linux-gnu-gcc-nm && \
        rm /usr/bin/x86_64-linux-gnu-gcc-ranlib && \
        ln -s gcc-ranlib /usr/bin/x86_64-linux-gnu-gcc-ranlib

RUN mkdir -p /workspace/bin && \
        chmod 1777 /workspace && \
        mkdir /workspace/package

COPY compile.sh /workspace/bin/compile.sh
COPY prepare_dep.sh /workspace/bin/prepare_dep.sh
COPY prepare_user.sh /workspace/bin/prepare_user.sh

RUN chmod +x /workspace/bin/*
