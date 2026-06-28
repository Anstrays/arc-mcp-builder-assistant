"""Setuptools build hook for staging reviewed package resources."""

import importlib.util
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py

ROOT = Path(__file__).resolve().parent
BUILD_SUPPORT = ROOT / "build_support.py"


def _load_copy_helper():
    spec = importlib.util.spec_from_file_location("arc_builder_build_support", BUILD_SUPPORT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load build helper: {BUILD_SUPPORT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.copy_package_resources


copy_package_resources = _load_copy_helper()


class BuildPy(_build_py):
    """Build Python modules, then add the reviewed static resources."""

    def run(self) -> None:
        super().run()
        copy_package_resources(ROOT, Path(self.build_lib) / "arc_builder_kit")


setup(cmdclass={"build_py": BuildPy})
