import unittest

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

from haascli import __version__


class UnitTest(TestCommand):

    def initialize_options(self):
        TestCommand.initialize_options(self)

    def finalize_options(self):
        TestCommand.finalize_options(self)

    def run_tests(self):
        test_loader = unittest.TestLoader()
        test_suite = test_loader.discover('tests')
        runner = unittest.runner.TextTestRunner()
        runner.run(test_suite)

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
    cmdclass={'test': UnitTest},
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
