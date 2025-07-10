#!/usr/bin/env python3
"""
Setup script for YouTube Chapters Generator
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Read development requirements
dev_requirements = []
if os.path.exists("requirements-dev.txt"):
    with open("requirements-dev.txt", "r", encoding="utf-8") as fh:
        dev_requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="youtube-chapters",
    version="1.0.0",
    author="Dimitry Polivaev",
    author_email="",
    description="Generate chapter timecodes from YouTube videos using AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dpolivaev/youtube-chapters",
    packages=find_packages(),
    py_modules=["core", "config", "gui", "video_chapters"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Video",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
    },
    entry_points={
        "console_scripts": [
            "youtube-chapters=video_chapters:main",
            "youtube-chapters-gui=gui:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 