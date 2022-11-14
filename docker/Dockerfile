FROM ubuntu:20.04

# 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

COPY sources.list /etc/apt/sources.list

RUN DEBIAN_FRONTEND=noninteractive apt -y update && \
        DEBIAN_FRONTEND=noninteractive apt -y upgrade && \
        DEBIAN_FRONTEND=noninteractive apt -y install build-essential curl git wget libgmp-dev libmpfr-dev libmpc-dev python3-pip ninja-build cmake bison flex texinfo dpkg-dev devscripts

# prepare ld_hook
RUN cd /root && \
        mkdir ld_hook && \
        cd ld_hook && \
        git clone https://kongjiadongyuan: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@github.com/IAPCP/ld_hook.git && \
        mkdir build && \
        cd build && \
        ../ld_hook/configure --prefix=/usr && \
        make -j${nproc} && \
        make install

# prepare gcc_parser
RUN cd /root && \
        mkdir gcc_parser && \
        cd gcc_parser && \
        pip3 install robotpy-cppheaderparser && \
        git clone https://kongjiadongyuan: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@github.com/IAPCP/gcc_parser.git && \
        cd gcc_parser && \
        git checkout 9.3.0 && \
        cd .. && \
        mkdir build && \
        cd build && \
        ../gcc_parser/configure --prefix=/usr -enable-language=c,c++ --disable-multilib --disable-werror --disable-bootstrap && \
        make -j${nproc} && \
        make install && \
        rm /usr/lib/x86_64-linux-gnu/libstdc++.so.6 && \
        ln -s /usr/lib64/libstdc++.so.6 /usr/lib/x86_64-linux-gnu/libstdc++.so.6

COPY compile.sh /root/compile.sh
RUN chmod +x /root/compile.sh
