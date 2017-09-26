from setuptools import setup, find_packages

from haascli import __version__
import unittest


def my_test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests')
    return test_suite


setup_options = dict(
    name='haascli',
    version=__version__,
    description='Universal Command Line Environment for HAAS.',
    long_description=open('README.rst').read(),
    author='NCSU Operating Research Lab',
    url='https://github.com/vin0110/haas',
    scripts=['bin/haas'],
    packages=find_packages(exclude=['tests*']),
    package_data={'haascli': ['examples/*/*.rst']},
    test_suite='setup.my_test_suite',
    install_requires=[
        'boto3',
        'click',
        'executor',
        'troposphere',
        'awacs',
    ],
    extras_require={
        ':python_version=="3.4"': [
            'click>=6.7',
        ]
    },
    license="Apache License 2.0",
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ),
)

setup(**setup_options)
