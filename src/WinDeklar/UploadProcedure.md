To upload a new version to PyPi do:

1. change version number in setup.py and pyproject.toml
2. run python -m build
3. delete the old version *.gz and *.gz in dist directory
4. push changes
5. in https://github.com/njodal/WinDeklar/releases press Draft new release (use the same version number as in setup.py)
6. this should be all, just in case see https://github.com/njodal/WinDeklar/actions the status and here in https://pypi.org/project/WinDeklar/ PyPi
