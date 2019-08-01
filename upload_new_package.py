"""
PyPi package uploader that doesn't return a bad status code
if the package already exists.
"""
import sys

from requests import HTTPError
from twine.cli import dispatch


def main():
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
