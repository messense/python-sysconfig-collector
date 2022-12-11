import os
import sys
import json
from collections import defaultdict
import subprocess


ARCHES = ["i686"]
PY_VERS = [
    "cp36-cp36m",
    "cp37-cp37m",
    "cp38-cp38",
    "cp39-cp39",
    "cp310-cp310",
    "cp311-cp311",
    "pp37-pypy37_pp73",
    "pp38-pypy38_pp73",
    "pp39-pypy39_pp73",
]


def manylinux():
    well_known = defaultdict(list)
    cwd = os.getcwd()
    for arch in ARCHES:
        docker_image = f"quay.io/pypa/manylinux2014_{arch}"
        for ver in PY_VERS:
            # PyPy is not available on ppc64le & s390x
            if arch in ["ppc64le", "s390x"] and ver.startswith("pp"):
                continue
            command = [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{cwd}:/io",
                "-w",
                "/io",
                docker_image,
                f"/opt/python/{ver}/bin/python",
                "/io/get_interpreter_metadata.py",
            ]
            try:
                metadata = subprocess.check_output(command).decode().strip()
            except subprocess.CalledProcessError as exc:
                print(exc.output, file=sys.stderr)
                raise
            metadata = json.loads(metadata.splitlines()[-1])
            for key in ["system", "platform"]:
                metadata.pop(key, None)
            well_known[arch].append(metadata)
    return well_known


def fedora():
    pythons = [
        "python3.6",
        "python3.7",
        "python3.8",
        "python3.9",
        "python3.10",
        "python3.11",
        "python3.12",
        "pypy3.7",
        "pypy3.8",
        "pypy3.9",
    ]
    sysconfig = defaultdict(list)
    cwd = os.getcwd()
    # PyPy is not available on ppc64le & s390x via manylinux => use Fedora's
    for arch in ["x86_64", "aarch64", "armv7l", "ppc64le", "s390x"]:
        docker_image = f"fedora_{arch}"
        for python in pythons:
            command = [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{cwd}:/io",
                "-w",
                "/io",
                docker_image,
                python,
                "/io/get_interpreter_metadata.py",
            ]
            try:
                metadata = subprocess.check_output(command).decode().strip()
            except subprocess.CalledProcessError as exc:
                print("Error: " + exc.output.decode(), file=sys.stderr)
                if arch == "aarch64" and python == "pypy3.9":
                    # qemu-aarch64: /usr/bin/pypy3.9: Invalid note in PT_GNU_PROPERTY
                    # hardcode it for now
                    metadata = {
                        "major": 3,
                        "minor": 9,
                        "abiflags": "",
                        "interpreter": "pypy",
                        "ext_suffix": ".pypy39-pp73-aarch64-linux-gnu.so",
                        "abi_tag": "pp73",
                        "pointer_width": 64,
                    }
                else:
                    continue
            if isinstance(metadata, str):
                metadata = json.loads(metadata.splitlines()[-1])
            for key in ["system", "platform"]:
                metadata.pop(key, None)
            sysconfig[arch].append(metadata)
            if arch == "armv7l":
                # armv6l metadata is the same as armv7l
                sysconfig["armv6l"].append(metadata)
    return sysconfig


def main():
    well_known = manylinux()
    # Merge sysconfig from Fedora for architectures lacking manylinux docker image
    for arch, metadatas in fedora().items():
        well_known[arch].extend(metadatas)

    with open("sysconfig-linux.json", "w") as f:
        f.write(json.dumps(well_known, indent=2))


if __name__ == "__main__":
    main()
