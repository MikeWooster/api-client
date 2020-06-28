"""
PyPi package uploader that doesn't return a bad status code
if the package already exists.
"""
import sys

from requests import HTTPError
from twine.cli import dispatch

VERSION_FILE = "VERSION"


def main():
    print("Uploading to pypi")
    upload_to_pypi()


def upload_to_pypi():
    try:
        return dispatch(["upload", "dist/*"])
    except HTTPError as error:
        handle_http_error(error)


def handle_http_error(error: HTTPError):
    try:
        if error.response.status_code == 400:
            print(error)
        else:
            raise error
    except Exception:
        raise error


if __name__ == "__main__":
    sys.exit(main())
