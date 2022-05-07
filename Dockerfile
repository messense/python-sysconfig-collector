FROM ubuntu:20.04

RUN apt-get update && \
  apt-get install -y --no-install-recommends python3 software-properties-common && \
  add-apt-repository ppa:deadsnakes/ppa && \
  add-apt-repository ppa:pypy/ppa && \
  apt-get update && \
  apt-get install -y python3.6 python3.7 python3.9 python3.10 pypy3
