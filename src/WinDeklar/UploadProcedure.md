To upload a new version to PyPi do:

1. change version number in setup.py and pyproject.toml
2. run python -m build (in WinDeklar directory)
3. delete the old version *.gz and *.gz in dist directory
4. push changes
5. in https://github.com/njodal/WinDeklar/releases press Draft new release (maker sure to create a new version number)
6. this should be all, just in case see https://github.com/njodal/WinDeklar/actions the status and here in https://pypi.org/project/WinDeklar/ PyPi
7. remember the last step can take a few minutes