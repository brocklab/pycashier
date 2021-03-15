import io
import os
import re

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# ==============================================================================
# Utilities
# ==============================================================================


def read(path, encoding="utf-8"):
    path = os.path.join(os.path.dirname(__file__), path)
    with io.open(path, encoding=encoding) as fp:
        return fp.read()


def get_install_requirements(path):
    content = read(path)
    return [
        req for req in content.split("\n")
        if req != "" and not req.startswith("#")
    ]


def version(path):
    """Obtain the package version from a python file e.g. pkg/__init__.py

    See <https://packaging.python.org/en/latest/single_source_version.html>.
    """
    version_file = read(path)
    version_match = re.search(r"""^__version__ = ['"]([^'"]*)['"]""",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


HERE = os.path.abspath(os.path.dirname(__file__))

setup(
    name="pycashier",
    version=version("cashier/__init__.py"),
    description="cashier: cash in on expressed barcode tags",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="Daylin Morgan",
    author_email="daylinmorgan@gmail.com",
    download_url="http://github.com/DaylinMorgan/pycashier/",
    license="BSD 3-clause",
    #packages=find_packages(),
    packages=['cashier'],
    entry_points={"console_scripts": ['cashier = cashier.cashier:main']},
    include_package_data=True,
    install_requires=get_install_requirements("requirements.txt"),
    python_requires=">=3.6",
    #extras_require={"dev": get_install_requirements("requirements_dev.txt")},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
