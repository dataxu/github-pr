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
    entry_points={
        'console_scripts': [
            'github-pr = github_pr:main',
        ]
    },
    install_requires=[
        'argparse==1.3.0',
        'PyGithub>=1.25.2',
        'wsgiref==0.1.2',
        'tabulate==0.7.5'
    ],
    setup_requires=[
        'argparse',
        'PyGithub',
        'wsgiref',
        'tabulate'
    ],
    url='https://github.com/dataxu/github-pr',
    version='1.2.1',
    scripts=['github_pr.py'],
    keywords=['github'],
)
