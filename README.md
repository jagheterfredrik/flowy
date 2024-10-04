# Flowy
Building Openpilot Python dependencies for native Android. Hopes to remove the need for Termux. Incomplete but compiling.

## Install docker with rootless
sudo apt install docker.io
sudo usermod -aG docker $USER

## Build docker container
docker build -t builder docker/

## Build apk
./build.sh