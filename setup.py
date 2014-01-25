import os
from setuptools import setup
from explorer import __version__

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "django-sql-explorer",
    version = __version__,
    author = "Chris Clark",
    author_email = "chris@untrod.com",
    description = ("A pluggable app that allows admins to execute SQL"
		   " and view and export the results. Inspired by Stack Exchange Data Explorer."),
    license = "MIT",
    keywords = "django sql explorer reports reporting csv",
    url = "https://github.com/epantry/django-sql-explorer",
    packages=['explorer'],
    long_description=read('README.rst'),
    classifiers=[
        "Topic :: Utilities",
    ],
    install_requires=[
        'Django>=1.4',
    ],
    include_package_data=True,
    zip_safe = False,
)
