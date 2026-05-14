"""
Compatibility shim for package-name collision.

This repo has a local ``graphql`` package path for service code, which can
shadow the external ``graphql`` dependency (graphql-core). We delegate loading
to the external package in site-packages.
"""

from __future__ import annotations

import importlib.machinery
import pathlib
import sys


def _load_external_graphql_into_current_module() -> None:
    current_file = pathlib.Path(__file__).resolve()
    project_root = current_file.parent.parent  # /app

    spec = None
    for raw_path in sys.path:
        if not raw_path:
            continue
        try:
            resolved = pathlib.Path(raw_path).resolve()
        except (OSError, RuntimeError):
            continue
        if resolved == project_root:
            continue

        found = importlib.machinery.PathFinder.find_spec('graphql', [str(resolved)])
        if found and found.loader and found.origin:
            try:
                if pathlib.Path(found.origin).resolve() != current_file:
                    spec = found
                    break
            except (OSError, RuntimeError):
                spec = found
                break

    if spec is None or spec.loader is None:
        raise ImportError('Unable to load external graphql package from site-packages')

    module = sys.modules[__name__]
    module.__file__ = spec.origin
    module.__loader__ = spec.loader
    module.__package__ = spec.parent or __name__
    module.__spec__ = spec
    if spec.submodule_search_locations is not None:
        module.__path__ = list(spec.submodule_search_locations)
    spec.loader.exec_module(module)


_load_external_graphql_into_current_module()
