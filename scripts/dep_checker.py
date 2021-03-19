"""
Checks tested dependencies against latest releases to ensure that the
tox matrix includes all latest versions.

A system exit is a valid way to exit this script and indicates a failure.
"""
import subprocess
from dataclasses import dataclass
from typing import Dict, Union, Optional, List
from packaging import version


@dataclass
class Package:
    name: str
    current: Union[version.LegacyVersion, version.Version]
    latest: Union[version.LegacyVersion, version.Version]


@dataclass
class ToxDep:
    name: str
    gte: Union[version.LegacyVersion, version.Version]
    lt: Union[version.LegacyVersion, version.Version]


@dataclass
class ToxEnv:
    name: str
    deps: List[ToxDep]


@dataclass
class ToxFile:
    envs: List[ToxEnv]


def main():
    packages = get_current_packages()
    toxfile = readtox()

    deps = ["requests", "tenacity"]
    for dep in deps:
        check_version(packages[dep], toxfile)


def get_current_packages() -> Dict[str, Package]:
    # Get all currently installed packages and the latest version available on pypi.
    packages = get_outdated_packages()
    packages.update(get_uptodate_packages())
    return packages


def check_version(package: Package, toxfile: ToxFile):
    print(f"checking package is covered in tox file: {package}")
    if not version_in_tox_file(package, toxfile):
        msg = f"latest version of package not in tox file: {package.name} - version {package.latest}"
        print(msg)
        raise SystemExit(msg)


def version_in_tox_file(package: Package, toxfile: ToxFile) -> bool:
    covered = False

    for env in toxfile.envs:
        for dep in env.deps:
            if dep.name != package.name:
                continue

            if package.latest >= dep.gte and package.latest < dep.lt:
                covered = True

    return covered


def readtox() -> ToxFile:
    envs: List[ToxEnv] = []
    resp = run("tox --showconfig")
    for env in resp.decode("utf-8").split("\n\n"):
        envs.append(parse_toxenv(env))
    return ToxFile(envs=envs)


def parse_toxenv(text: str) -> ToxEnv:
    env = ToxEnv(name="", deps=[])

    for line in text.split("\n"):
        if line.startswith("[") and line.endswith("]"):
            env.name = line

        if line.startswith("deps"):
            env.deps = parse_toxdeps(line)

    return env


def parse_toxdeps(text: str) -> List[ToxDep]:
    toxdeps = []

    _, deps = text.split("=", 1)
    for dep in deps.strip().rstrip("]").lstrip("[").split(", "):
        try:
            dep = extractdep(dep)
        except Exception as err:
            print(f"cannot parse: {dep}")
            continue
        toxdeps.append(dep)

    return toxdeps


def extractdep(dep: str) -> ToxDep:
    parts = dep.replace(">", "=").replace("<", "=").split("=")
    name = parts[0]
    gte = parts[2].strip(" ,")
    lt = parts[3].strip(" ,")
    return ToxDep(name=name, gte=version.parse(gte), lt=version.parse(lt))


def get_outdated_packages() -> Dict[str, Package]:
    packages = {}

    resp = run("pip list -o")

    for line in resp.decode("utf-8").split("\n"):
        try:
            package = _parse_outdated_version_line(line)
        except Exception as err:
            print(f"unable to parse version for package: {line}")
            continue

        packages[package.name] = package

    return packages


def _parse_outdated_version_line(line: str) -> Optional[Package]:
    name, current, latest, _ = line.split()
    return Package(name=name, current=version.parse(current), latest=version.parse(latest))


def get_uptodate_packages() -> Dict[str, Package]:
    packages = {}

    resp = run("pip list -u")

    for line in resp.decode("utf-8").split("\n"):
        try:
            package = _parse_uptodate_version_line(line)
        except Exception as err:
            print(f"unable to parse version for package: {line}")
            continue

        packages[package.name] = package

    return packages


def _parse_uptodate_version_line(line: str) -> Optional[Package]:
    name, current = line.split()
    # In this case, the current == latest versions
    return Package(name=name, current=version.parse(current), latest=version.parse(current))


def run(command: str) -> bytes:
    return subprocess.check_output(command.split())


if __name__ == "__main__":
    main()
