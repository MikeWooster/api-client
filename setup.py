#!/usr/bin/env python

import setuptools


application_dependencies = [
    "requests>=2.16",
    "pyyaml",
    "tenacity",
]
prod_dependencies = []
test_dependencies = [
    "pytest",
    "pytest-env",
    "pytest-cov",
    "vcrpy",
]
lint_dependencies = [
    "flake8",
    "flake8-docstrings",
    "black",
    "isort",
]
docs_dependencies = []
dev_dependencies = test_dependencies + lint_dependencies + docs_dependencies + [
    "ipdb",
]


with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="api-client",
    version="1.1.0",
    description="Separate the high level client implementation from the underlying CRUD.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Mike Wooster",
    author_email="",
    url="https://github.com/MikeWooster/api-client",
    python_requires=">=3.6",
    packages=[
        "apiclient",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
    ],
    install_requires=application_dependencies,
    extras_require={
        "production": prod_dependencies,
        "test": test_dependencies,
        "lint": lint_dependencies,
        "docs": dev_dependencies,
        "dev": dev_dependencies,
    },
    include_package_data=True,
    zip_safe=False,
)
