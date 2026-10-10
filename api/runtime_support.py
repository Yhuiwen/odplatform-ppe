"""Load installed frozen Windows extensions without changing either environment."""
import os
import sys
from pathlib import Path

_dll_handles = []


def append_business_runtime(packages):
    packages = Path(packages)
    if not packages.is_dir():
        return
    paths = [packages]
    if os.name == 'nt':
        paths += [packages / 'win32', packages / 'win32' / 'lib', packages / 'pythonwin']
    for path in paths:
        if path.is_dir() and str(path) not in sys.path:
            sys.path.append(str(path))
    dll_path = packages / 'pywin32_system32'
    if os.name == 'nt' and dll_path.is_dir():
        # Keep the handle alive: closing it removes the DLL search directory.
        _dll_handles.append(os.add_dll_directory(str(dll_path)))
