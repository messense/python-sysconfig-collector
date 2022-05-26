import platform
import json
import sys
from collections import defaultdict
import subprocess

MIN_MINOR_VER = 6
MAX_MINOR_VER = 11

PY_IMPLS = ["python", "pypy"]
ARCH_ALIAS = {
    "amd64": "x86_64",
    "arm64": "aarch64",
}
OS_ALIAS = {
    "darwin": "macos",
}


def main():
    machine = platform.machine().lower()
    arch = ARCH_ALIAS.get(machine, machine)
    plat = platform.system().lower()
    os = OS_ALIAS.get(plat, plat)
    if os == "windows":
        py_arches = ["64", "32"]
    else:
        py_arches = ["64"]

    well_known = defaultdict(list)
    for impl in PY_IMPLS:
        for minor in range(MIN_MINOR_VER, MAX_MINOR_VER + 1):
            for py_arch in py_arches:
                if os == "windows":
                    if impl == "pypy":
                        # py.exe doesn't support finding pypy
                        continue
                    command = [
                        "py",
                        f"-3.{minor}-{py_arch}",
                        "get_interpreter_metadata.py",
                    ]
                    if py_arch == "32":
                        arch = "i686"
                    else:
                        arch = "x86_64"
                else:
                    command = [f"{impl}3.{minor}", "get_interpreter_metadata.py"]
                try:
                    metadata = subprocess.check_output(command).decode().strip()
                except FileNotFoundError:
                    print(f"{impl}3.{minor} not found, skipped.", file=sys.stderr)
                    continue
                except subprocess.CalledProcessError as exc:
                    print(exc.output.decode(), file=sys.stderr)
                    continue
                metadata = json.loads(metadata.splitlines()[-1])
                for key in ["system", "platform"]:
                    metadata.pop(key, None)
                well_known[arch].append(metadata)

                # on macOS the sysconfig we care about are the same on x86_64 and aarch64
                # so we can just duplicate it
                #
                # Note that pypy doesn't support aarch64 macOS yet
                if os == "macos" and impl != "pypy":
                    if arch == "x86_64":
                        well_known["aarch64"].append(metadata)
                    elif arch == "aarch64":
                        well_known["x86_64"].append(metadata)
                # Windows aarch64 uses `win_arm64` instead of `win_amd64` in ext_suffix
                # Python only have official support for aarhc64 Windows on 3.11+
                elif os == "windows" and impl != "pypy" and minor >= 11:
                    if arch == "x86_64":
                        arm64_metadata = metadata.copy()
                        arm64_metadata["ext_suffix"] = arm64_metadata[
                            "ext_suffix"
                        ].replace("win_amd64", "win_arm64")
                        well_known["aarch64"].append(arm64_metadata)

    with open(f"sysconfig-{os}.json", "w") as f:
        f.write(json.dumps(well_known, indent=2))


if __name__ == "__main__":
    main()
