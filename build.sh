#!/bin/bash
rm -rf dist
mkdir -p dist

python setup.py sdist
twine upload dist/*