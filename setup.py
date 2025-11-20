"""
REROUTE Setup Configuration

File-based routing for Python backend frameworks.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="reroute",
    version="0.1.0",

    description="File-based routing for Python backend frameworks (FastAPI, Flask)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="C B Sajan",
    author_email="cloud.ckhathri@gmail.com",
    url="https://github.com/cbsajan/reroute",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "reroute.cli": ["templates/*.j2"],
    },
    install_requires=[
        "click>=8.0.0",
        "questionary>=2.0.0",
        "jinja2>=3.0.0",
    ],
    extras_require={
        "fastapi": ["fastapi>=0.100.0", "uvicorn[standard]>=0.20.0"],
        "flask": ["flask>=2.0.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "reroute=reroute.cli.commands:cli",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: FastAPI",
        "Framework :: Flask",
    ],
    keywords="fastapi flask routing file-based web-framework",
)
