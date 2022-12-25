import os

from setuptools import setup

__version__ = "0.0.1"
__author__ = "osoken"
__description__ = "A Simple python package to apply typing to iterables."
__email__ = "osoken.devel@outlook.jp"
__package_name__ = "typingiterable"

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"), "r", encoding="utf-8") as fin:
    __long_description__ = fin.read()

setup(
    name=__package_name__,
    version=__version__,
    author=__author__,
    author_email=__email__,
    license="MIT",
    url="https://github.com/osoken/typingiterable",
    description=__description__,
    long_description=__long_description__,
    long_description_content_type="text/markdown",
    packages=[__package_name__],
    install_requires=[],
    extras_require={"dev": ["flake8", "pytest", "black", "mypy", "tox", "isort", "pytest-mock"]},
)
