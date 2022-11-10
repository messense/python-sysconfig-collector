import os
import sys
import json
from collections import defaultdict
import subprocess


ARCHES = ["x86_64", "i686", "aarch64", "ppc64le", "s390x"]
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


def armv7l():
    docker_image = "python-armv7l"
    pythons = [
        "python3.6",
        "python3.7",
        "python3.8",
        "python3.9",
        "python3.10",
        "python3.11",
        "pypy3",
    ]
    cwd = os.getcwd()
    sysconfig = {"armv7l": [], "armv6l": []}
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
            print(exc.output, file=sys.stderr)
            raise
        metadata = json.loads(metadata.splitlines()[-1])
        for key in ["system", "platform"]:
            metadata.pop(key, None)
        sysconfig["armv7l"].append(metadata)
        # armv6l metadata is the same as armv7l
        sysconfig["armv6l"].append(metadata)
    return sysconfig


def condaforge_ppc64le():
    sysconfig = defaultdict(list)
    cwd = os.getcwd()
    # PyPy is not available on ppc64le via manylinux; use conda-forge instead
    for arch in ["ppc64le"]:
        docker_image = f"condaforge_{arch}"
        for ver in PY_VERS:
            if not ver.startswith("pp"):
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
            sysconfig[arch].append(metadata)
    return sysconfig


def main():
    well_known = manylinux()
    for sysconfig in (armv7l(), condaforge_ppc64le()):
        for arch, metadatas in sysconfig.items():
            well_known[arch].extend(metadatas)
    with open("sysconfig-linux.json", "w") as f:
        f.write(json.dumps(well_known, indent=2))


if __name__ == "__main__":
    main()
