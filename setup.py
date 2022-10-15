#!/usr/bin/env python

"""The setup script."""

from typing import List

from setuptools import find_packages, setup

with open("README.rst", encoding="utf-8") as readme_file:
    readme = readme_file.read()

requirements: List[str] = []

test_requirements: List[str] = []

setup(
    author="José Parera",
    author_email="j3parera@gmail.com",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="Python implementation of MERG CBUS Protocol.",
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    include_package_data=True,
    keywords="mpi_cbus",
    name="mpi_cbus",
    packages=find_packages(include=["mpi_cbus", "mpi_cbus.*"]),
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/j3parera/mpi_cbus",
    version="0.1.0",
    zip_safe=False,
)
