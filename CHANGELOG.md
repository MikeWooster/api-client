# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 2.0.0

### Added
- Support for Python 3.10 through 3.14.
- A `py.typed` marker so type checkers use the bundled inline type hints (#77).
- A wheel is now published alongside the source distribution.

### Changed
- Minimum supported Python is now 3.10.
- Type hints modernised to use PEP 604 unions (`X | None`) and built-in generics.
- `clone()` preserves attributes set in subclass constructors (#73).
- `@endpoint` includes inherited attributes and ignores methods and functions (#68).
- **Breaking:** paginator `next_page` callbacks now receive a `Response` object instead of the
  decoded body. Use `response.get_json()` for the body and `response.get_original()` for the
  underlying response (e.g. headers and links) (#86).

### Removed
- Support for Python 3.6, 3.7, 3.8 and 3.9.
- The `OptionalDict`, `OptionalStr`, `OptionalInt` and `OptionalJsonType` aliases from `apiclient.utils.typing` (use `X | None` directly).

### Fixed
- Unrelated exceptions are no longer masked as `UnexpectedError`; only request errors are wrapped (#80).
- `post()`, `put()` and `patch()` type hints accept JSON arrays, not just objects (#90).
- `paginators` imports `APIClient` from `apiclient.client` instead of the package root (#78).
