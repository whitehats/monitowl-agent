# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(
    name="monitowl-agent",
    version="5",
    description="MonitOwl.com Agent software",
    long_description=open("README.rst").read(),
    license="Apache Software License",
    author="MonitOwl",
    author_email="office@monitowl.com",
    url="http://monitowl.com",
    packages=find_packages(),
    install_requires=open("requirements.txt").read().split("\n"),
    tests_require=["pytest"],
    scripts=["bin/monitowl-agent"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: Apache Software License",
    ]
)
