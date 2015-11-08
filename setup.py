#!/usr/bin/env python
# -*- coding: utf-8 -*-

with open('requirements.txt', 'r') as f:
    requires = [x.strip() for x in f if x.strip()]

with open('README.md', 'r') as f:
    readme = f.read()


setup(
    name='office_weather',
    version='0.1.0',
    description="Office weather monitor",
    long_description=readme,
    url='https://github.com/frennkie/office_weather',
    license='MIT License',
    classifiers=(
        'Programming Language :: Python :: 2.7',
    ),
)
