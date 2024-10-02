FROM ubuntu:24.04

RUN sudo apt install capnproto pkg-config m4 libtool automake autoconf openjdk-17-jdk patchelf python3-virtualenv unzip libssl-dev libgdbm-compat-dev liblzma-dev libbz2-dev cmake
RUN python -m venv venv
RUN source venv/bin/activate
RUN pip install buildozer setuptools cython

CMD 