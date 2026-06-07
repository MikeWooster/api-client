.PHONY: test lint format check

test:
	pytest

lint:
	isort apiclient tests --check-only
	black --check apiclient tests
	flake8 apiclient tests

format:
	isort apiclient tests
	black apiclient tests

check: lint test
