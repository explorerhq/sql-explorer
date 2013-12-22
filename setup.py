import os
from setuptools import setup
from report import __version__

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "django-sql-reports",
    version = __version__,
    author = "Chris Clark",
    author_email = "cc@epantry.com",
    description = ("a pluggable app that allows admins to execute sql"
		   " and view and export the results. Loosely inspired by Stack Exchange Data Explorer."),
    license = "MIT",
    keywords = "django sql reports reporting csv",
    url = "https://github.com/epantry/django-sql-reports",
    packages=['report'],
    long_description=read('README.md'),
    classifiers=[
        "Topic :: Utilities",
    ],
    install_requires=[
        'Django>=1.4',
    ],
    include_package_data=True,
    zip_safe = False,
)
