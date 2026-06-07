# Contributing

## Development setup

The library supports Python 3.9 to 3.14. Create a virtual environment and
install the package with its development dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Tests and linting

A `Makefile` wraps the same commands CI runs:

```bash
make test      # run the test suite (with the 100% coverage gate)
make lint      # check formatting and style (isort, black, flake8)
make format    # apply isort and black fixes
make check     # lint + test — run this before pushing
```

CI runs `lint` and the test suite across every supported Python version on
each pull request. A green `make check` locally means a green pipeline.

## Releasing

Releases publish to [PyPI](https://pypi.org/project/api-client/) automatically
when a GitHub Release is published, using
[PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) over OIDC
(no API tokens or passwords are stored).

To release:

1. Bump the version in the `VERSION` file in a pull request and merge it.
2. Publish a GitHub Release whose tag is `v<VERSION>`
   (for example, `v1.4.0` for `VERSION` `1.4.0`).

Publishing the release triggers the `Python test and deploy` workflow, which
runs the full test suite, verifies the tag matches `VERSION`, builds the sdist
and wheel, and publishes them to PyPI. A tag that does not match `VERSION`
fails the release before anything is published.

For a pre-release, tag it as a PEP 440 pre-release (for example, `v1.4.0rc1`,
with `VERSION` set to `1.4.0rc1`) and tick the "Set as a pre-release" box on the
GitHub Release.
