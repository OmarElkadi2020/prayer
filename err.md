python3 -m src
Traceback (most recent call last):
  File "/usr/lib/python3.10/runpy.py", line 196, in _run_module_as_main
    return _run_code(code, main_globals, None,
  File "/usr/lib/python3.10/runpy.py", line 86, in _run_code
    exec(code, run_globals)
  File "/home/omar/private/prayer/src/__main__.py", line 8, in <module>
    from src.config.security import get_asset_path, load_config, LOG, parse_args
  File "/home/omar/private/prayer/src/config/security/__init__.py", line 26, in <module>
    DEFAULT_ADHAN_PATH = get_asset_path('adhan.wav')
  File "/home/omar/private/prayer/src/config/security/__init__.py", line 23, in get_asset_path
    return resources.files('assets').joinpath(filename)
  File "/usr/lib/python3.10/importlib/_common.py", line 22, in files
    return from_package(get_package(package))
  File "/usr/lib/python3.10/importlib/_common.py", line 66, in get_package
    resolved = resolve(package)
  File "/usr/lib/python3.10/importlib/_common.py", line 57, in resolve
    return cand if isinstance(cand, types.ModuleType) else importlib.import_module(cand)
  File "/usr/lib/python3.10/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
ModuleNotFoundError: No module named 'assets'