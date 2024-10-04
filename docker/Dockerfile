FROM ubuntu:24.04

RUN apt update && apt install -y capnproto pkg-config m4 libtool automake autoconf openjdk-17-jdk patchelf python3-venv unzip libssl-dev libgdbm-compat-dev liblzma-dev libbz2-dev cmake zlib1g-dev git python3-pip
RUN useradd -m -U builder
RUN apt install -y swig zip
USER builder
RUN python3 -m venv ~/.venv
RUN ~/.venv/bin/pip install buildozer setuptools cython
