# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.4.0

### Added
- Support for Python 3.10 through 3.14.
- A wheel is now published alongside the source distribution.

### Changed
- Minimum supported Python is now 3.10.
- `clone()` preserves attributes set in subclass constructors (#73).
- `@endpoint` includes inherited attributes and ignores methods and functions (#68).

### Removed
- Support for Python 3.6, 3.7, 3.8 and 3.9.

### Fixed
- Unrelated exceptions are no longer masked as `UnexpectedError`; only request errors are wrapped (#80).
- `post()`, `put()` and `patch()` type hints accept JSON arrays, not just objects (#90).
- `paginators` imports `APIClient` from `apiclient.client` instead of the package root (#78).
