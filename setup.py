#!/usr/bin/env python

from setuptools import setup

setup(
    name="ttbp",
    version="0.12.3",
    description="command line social blogging tool used on tilde.town",
    url="https://github.com/modgethanc/ttbp",
    author="~endorphant, hyperreal",
    author_email="endorphant@tilde.town, hyperreal@moonshadow.dev",
    license="MIT",
    classifiers=[
        "Topic :: Artistic Software",
        "License :: OSI Approved :: MIT License",
    ],
    keywords="blog",
    packages=["ttbp"],
    install_requires=["inflect==0.2.5", "mistune==0.8.1", "colorama==0.3.9", "six"],
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "feels = ttbp.ttbp:main",
            "ttbp = ttbp.ttbp:main",
        ]
    },
)
