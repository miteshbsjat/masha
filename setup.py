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
    install_requires=[
        "pyyaml>=6.0.2",
        "toml>=0.10.2",
        "result>=0.17.0",
        "pydantic>=2.10.6",
        "Jinja2>=3.1.5",
        "returns>=0.24.0",
        "click>=8.1.8",
    ],                            # list all packages that your package uses
    entry_points='''
        [console_scripts]
        masha=masha.cli:main
    ''',
    keywords=["pypi", "masha", "shell", "yaml", "json", "jinja2", "configuration"],           #descriptive meta-data
    classifiers=[                                   # https://pypi.org/classifiers
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        "Topic :: Software Development :: Code Generators",
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
        "Programming Language :: Python :: 3 :: Only",
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
    
    download_url=f"https://github.com/miteshbsjat/masha/archive/refs/tags/{__version__}.tar.gz",
    cmdclass={'test': Run_TestSuite},
)