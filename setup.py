from setuptools import setup, find_packages

setup_args = {
    "name": "cadquery_massembly",
    "version": "1.0.0rc1",
    "description": "A manual assembly system for cadquery based on mates",
    "include_package_data": True,
    "install_requires": [],
    "packages": find_packages(),
    "zip_safe": False,
    "author": "Bernhard Walter",
    "author_email": "b_walter@arcor.de",
    "url": "https://github.com/bernhard-42/cadquery-massembly",
    "keywords": ["cadquery"],
    "classifiers": [
        "Development Status :: 4 - Beta",
        "Framework :: IPython",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Multimedia :: Graphics",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
}

setup(**setup_args)
