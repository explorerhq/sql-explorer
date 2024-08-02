import os
import sys
from pathlib import Path

from setuptools import setup
try:
    from sphinx.setup_command import BuildDoc
except ImportError:
    BuildDoc = None

from explorer import get_version


name = "django-sql-explorer"
version = get_version()
release = get_version(True)


def requirements(fname):
    path = os.path.join(os.path.dirname(__file__), "requirements", fname)
    with open(path) as f:
        return f.read().splitlines()


if sys.argv[-1] == "build":
    os.system("python setup.py sdist bdist_wheel")
    print(f"Built release {release} (version {version})")
    sys.exit()

if sys.argv[-1] == "release":
    os.system("twine upload --skip-existing dist/*")
    sys.exit()

if sys.argv[-1] == "tag":
    print("Tagging the version:")
    os.system(f"git tag -a {version} -m 'version {version}'")
    os.system("git push --tags")
    sys.exit()

this_directory = Path(__file__).parent
long_description = (this_directory / "README.rst").read_text()

setup(
    name=name,
    version=version,
    author="Chris Clark",
    author_email="chris@sqlexplorer.io",
    maintainer="Chris Clark",
    maintainer_email="chris@sqlexplorer.io",
    description=("SQL Reporting that Just Works. Fast, simple, and confusion-free."
                 "Write and share queries in a delightful SQL editor, with AI assistance"),
    license="MIT",
    keywords="django sql explorer reports reporting csv json database query",
    url="https://www.sqlexplorer.io",
    project_urls={
      "Changes": "https://django-sql-explorer.readthedocs.io/en/latest/history.html",
      "Documentation": "https://django-sql-explorer.readthedocs.io/en/latest/",
      "Issues": "https://github.com/explorerhq/sql-explorer/issues"
    },
    packages=["explorer"],
    long_description=long_description,
    long_description_content_type="text/x-rst",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Utilities",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
    ],
    python_requires=">=3.8",
    install_requires=[
        requirements("base.txt"),
    ],
    extras_require={
        "charts": requirements("extra/charts.txt"),
        "snapshots": requirements("extra/snapshots.txt"),
        "xls": requirements("extra/xls.txt"),
        "assistant": requirements("extra/assistant.txt"),
        "uploads": requirements("extra/uploads.txt"),
    },
    cmdclass={
        "build_sphinx": BuildDoc,
    },
    command_options={
        "build_sphinx": {
            "project": ("setup.py", name),
            "version": ("setup.py", version),
            "release": ("setup.py", release),
            "source_dir": ("setup.py", "docs"),
            "build_dir": ("setup.py", "./docs/_build")
        }
    },
    include_package_data=True,
    zip_safe=False,
)
