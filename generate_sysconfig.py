import platform
import json
import sys
from collections import defaultdict
import subprocess

MIN_MINOR_VER = 6
MAX_MINOR_VER = 10

PY_IMPLS = ["python", "pypy"]
ARCH_ALIAS = {
    "arm64": "aarch64",
}
OS_ALIAS = {
    "darwin": "macos",
}


def main():
    machine = platform.machine()
    arch = ARCH_ALIAS.get(machine, machine)
    plat = platform.system().lower()
    os = OS_ALIAS.get(plat, plat)

    well_known = defaultdict(list)
    for impl in PY_IMPLS:
        for minor in range(MIN_MINOR_VER, MAX_MINOR_VER + 1):
            executable = f"{impl}3.{minor}"
            command = [executable, "get_interpreter_metadata.py"]
            try:
                metadata = subprocess.check_output(command).decode().strip()
            except FileNotFoundError:
                print(f"{executable} not found, skipped.", file=sys.stderr)
                continue
            except subprocess.CalledProcessError as exc:
                print(exc.output, file=sys.stderr)
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

    with open(f"sysconfig-{os}.json", "w") as f:
        f.write(json.dumps(well_known, indent=2))


if __name__ == "__main__":
    main()
