"""
(c) Copyright 2015. DataXu, Inc. All Rights Reserved.

github-pr setup
"""

from setuptools import setup, find_packages

setup(
    name='github_pr',
    author='DataXu',
    author_email='mferrante@dataxu.com',
    description='Pull Request utility script',
    license='(c) Copyright 2015. DataXu, Inc. All Rights Reserved.',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'github-pr = github_pr.cli:main',
        ]
    },
    install_requires=[
        'argparse==1.3.0',
        'PyGithub==1.25.2',
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
    version='2.0.0',
    keywords=['github'],
)
