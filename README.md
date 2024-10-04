# Flowy

## Install docker with rootless
sudo apt install docker.io
sudo usermod -aG docker $USER

## Build docker container
docker build -t p4a2 docker/

## Build apk
./build.sh