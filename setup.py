"""
Setup script for FFIEC Data Collector package
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="ffiec-data-collector",
    version="2.0.0",
    author="Michael",
    description="Lightweight Python library for collecting bulk FFIEC CDR data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/call-report/ffiec-data-collector",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "python-dateutil>=2.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.990",
            "jupyter>=1.0.0",
            "notebook>=6.5.0",
            "build>=0.10.0",
            "twine>=4.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "sphinx-autodoc-typehints>=1.19.0",
            "myst-parser>=0.18.0",
            "nbsphinx>=0.8.0",
        ],
        "validation": [
            "jsonschema>=4.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "ffiec-download=ffiec_data_collector.cli:main",
            "ffiec-validate=ffiec_data_collector.thumbprint:validate_cli",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/call-report/ffiec-data-collector/issues",
        "Source": "https://github.com/call-report/ffiec-data-collector",
    },
)