"""
(c) Copyright 2015. DataXu, Inc. All Rights Reserved.

github-pr setup
"""

from setuptools import setup

setup(
    name='github-pr',
    author='DataXu',
    author_email='mferrante@dataxu.com',
    description='Pull Request utility script',
    license='(c) Copyright 2015. DataXu, Inc. All Rights Reserved.',
    install_requires=[
        'argparse==1.3.0',
        'PyGithub==1.25.2',
        'wsgiref==0.1.2'
    ],
    setup_requires=[
        'argparse',
        'PyGithub',
        'wsgiref'
    ],
    url='https://github.com/dataxu/github-pr',
    version='1.0.0',
    scripts=['github-pr'],
    keywords=['github'],
)
