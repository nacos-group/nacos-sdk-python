import io
import os
import sys
from shutil import rmtree

from setuptools import find_packages, setup, Command

import nacos

#  just run `python setup.py upload`
here = os.path.abspath(os.path.dirname(__file__))

with io.open(os.path.join(here, 'README.md'), encoding='UTF-8') as f:
    long_description = '\n' + f.read()


class UploadCommand(Command):
    """Support setup.py upload."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds...')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution...')
        os.system(
            '{0} setup.py sdist bdist_wheel --universal'.format(sys.executable))

        self.status('Uploading the package to PyPi via Twine...')
        os.system('twine upload dist/*')

        sys.exit()


setup(
    name="nacos-sdk-python",
    version=nacos.__version__,
    packages=find_packages(
        exclude=["test", "*.tests", "*.tests.*", "tests.*", "tests"]),
    url="https://github.com/nacos-group/nacos-sdk-python",
    license="Apache License 2.0",
    classifiers=[
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7"
    ],
    keywords=['nacos', 'nacos-sdk-python'],
    author="nacos",
    author_email="755063194@qq.com",
    description="Python client for Nacos.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[],
    # $ setup.py publish support.
    cmdclass={
        'upload': UploadCommand,
    },
    # python_requires='>=3.6',
    project_urls={
        'Documentation': 'https://github.com/nacos-group/nacos-sdk-python',
        'Source': 'https://github.com/nacos-group/nacos-sdk-python',
        'Nacos Open API Guide': 'https://nacos.io/en-us/docs/open-api.html'
    },
)
