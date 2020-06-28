"""
Automate the generation of release candidate versions
for rc/ named branches.
"""
import subprocess
import sys
from typing import List, Optional, Tuple

VERSION_FILE = "VERSION"


def main(github_ref: str):
    major, minor, patch, rc = extract_version_from_ref(github_ref)
    print(f"tagged version: {fmt_version(major, minor, patch, rc)}")
    versions = get_all_versions()

    if (major, minor, patch, rc) in versions:
        raise SystemExit(
            f"Unable to upload new version. version already exists: '{fmt_version(major, minor, patch, rc)}'"
        )
    cur_version = get_version()
    if cur_version != f"{major}.{minor}.{patch}":
        raise SystemExit(
            "Cannot upload tag version. it does not match the current version of the project: "
            f"current_version = {cur_version}, tag_version = {fmt_version(major, minor, patch)}"
        )
    if rc > 0:
        print("Tagged as RC version. Updating version file.")
        update_rc_version(rc)

    print(f"Version in VERSION file: {read_version()}")


def fmt_version(major: int, minor: int, patch: int, rc: int = 0):
    if rc > 0:
        return f"{major}.{minor}.{patch}"
    return f"{major}.{minor}.{patch}rc{rc}"


def extract_version_from_ref(ref: str) -> Tuple[int, int, int, int]:
    err = (
        f"invalid github ref, expecting in format `refs/tags/v<major>.<minor>.<patch>[rc<rc>]`, got: '{ref}'"
    )
    try:
        title, subtitle, version = ref.split("/")
    except ValueError:
        raise SystemExit(err)

    if title != "refs" or subtitle != "tags" or not version.startswith("v"):
        raise SystemExit(err)

    try:
        major, minor, patch, rc = split_ver(version[1:])
    except ValueError:
        raise SystemExit(err)

    return major, minor, patch, rc


def get_current_branch() -> str:
    p = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True)
    if p.returncode != 0:
        raise SystemExit("Unable to determine current git branch name")
    return p.stdout.decode("utf-8").strip()


def update_rc_version(rc_version):
    # Extract the first 8 chars of the git hash and create a new rc version
    version = get_version()
    update_version_file(version, rc_version)


def get_all_versions() -> List[Tuple[int, int, int, int]]:
    p = subprocess.run(["pip", "search", "api-client"], capture_output=True)
    if p.returncode != 0:
        raise SystemExit("Unable to determine current git branch name")

    # A list to contain the existing rc versions deployed
    versions = []

    resp = p.stdout.decode("utf-8").strip()
    for line in resp.split("\n"):
        elems = line.split()
        if elems[0] != "api-client":
            continue
        version = elems[1].strip("()")

        versions.append(split_ver(version))

    return versions


def split_ver(version: str) -> Tuple[int, int, int, int]:
    major, minor, patch = version.split(".")
    if "rc" in patch:
        patch, rc = patch.split("rc")
    else:
        rc = 0
    return int(major), int(minor), int(patch), int(rc)


def get_version() -> str:
    v = read_version()

    # version is symantic.  Need 3 parts and last part must be an integer
    # otherwise we cant update the version.
    parts = v.split(".")
    if len(parts) != 3 or not parts[2].isnumeric():
        raise SystemExit(f"version is invalid: '{v}'")
    return v


def read_version() -> str:
    with open(VERSION_FILE, "r") as buf:
        v = buf.read()
    return v


def update_version_file(version: str, rc_ver: int):
    with open(VERSION_FILE, "w") as buf:
        buf.write(f"{version}rc{rc_ver}")


if __name__ == "__main__":
    sys.exit(main(github_ref=sys.argv[1]))
