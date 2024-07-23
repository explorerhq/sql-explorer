- [x] Update HISTORY
- [x] Update README and check formatting with http://rst.ninjs.org/
- [x] Make sure any new files are included in MANIFEST.in
- [x] Update version number in `explorer/__init__.py`
- [x] Update any package dependencies in `setup.py`
- [x] Commit the changes and add the tag *in master*:
```
git add .
git commit -m "Release 1.0.0"
git tag -a "1.0.0"
git push
git push --tags
```

- Be sure to test the built JS source by running `npm run build` and setting `VITE_DEV_MODE = False` in settings.py

- [x] Check the PyPI listing page (https://pypi.python.org/pypi/django-sql-explorer) to make sure that the release
  went out and that the README is displaying properly.
