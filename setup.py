import setuptools
from setuptools.command.test import test as TestCommand
# from .version import __version__
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
exec(open('masha/version.py').read())


class Run_TestSuite(TestCommand):
    def run_tests(self):
        import os
        import sys

        py_version = sys.version_info[0]
        print('Python version from setup.py is', py_version)
        run_string = "make test"
        os.system(run_string)


setuptools.setup(
    name='masha',                                  # should match the package folder
    packages=['masha'],                            # should match the package folder
    version=__version__,                            # important for updates
    license='Apache License 2.0',                   # should match your chosen license
    description='MASHup of Configuration Loading from several file types and run yAsha like Jinja2 template rendition with Validation',
    long_description=long_description,              # loads your README.md
    long_description_content_type="text/markdown",     # README.md is of type 'text/markdown'
    author='Mitesh Singh Jat',
    author_email="@".join(["mitesh.singh.jat", "gmail" + ".com"]),
    url='https://github.com/miteshbsjat/masha', 
    project_urls = {                                # Optional
        "Bug Tracker": "https://github.com/miteshbsjat/masha/issues"
    },
    install_requires=[],                            # list all packages that your package uses
    keywords=["pypi", "masha", "shell"],           #descriptive meta-data
    classifiers=[                                   # https://pypi.org/classifiers
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: Software Development :: Documentation',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System',
        'Topic :: System :: Operating System',
        'Topic :: System :: Shells',
        'Topic :: System :: System Shells',
        'Topic :: System :: Systems Administration',
        'Topic :: Text Processing',
        'Topic :: Utilities',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    
    download_url="https://github.com/miteshbsjat/masha/archive/refs/tags/0.0.0.tar.gz",
    cmdclass={'test': Run_TestSuite},
)