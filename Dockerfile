FROM fedora:36

RUN dnf install -y \
  python3.6 python3.7 python3.8 python3.9 python3.10 python3.11 python3.12 \
  pypy3.7 pypy3.8 pypy3.9