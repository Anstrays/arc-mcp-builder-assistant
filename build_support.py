"""Build-time helpers for staging Arc Builder Kit package resources."""

from __future__ import annotations

import shutil
from pathlib import Path

RESOURCE_DIRS = ("templates", "config", "examples")
ALLOWED_SUFFIXES = {".html", ".js", ".json", ".md", ".py"}
ALLOWED_SPECIAL_NAMES = {".env.example"}
IGNORED_NAMES = {".DS_Store"}
IGNORED_SUFFIXES = {".log", ".pyc", ".pyo"}
FORBIDDEN_NAMES = {
    ".env",
    ".pypirc",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "id_rsa",
}
FORBIDDEN_SUFFIXES = {".key", ".p12", ".pem", ".pfx"}


class ResourceBuildError(RuntimeError):
    """Raised when package resources are missing or unsafe to stage."""


def _is_ignored(path: Path) -> bool:
    return (
        "__pycache__" in path.parts
        or path.name in IGNORED_NAMES
        or path.suffix.lower() in IGNORED_SUFFIXES
    )


def _validate_resource(path: Path, source_root: Path) -> None:
    relative = path.relative_to(source_root)
    lowered_parts = {part.lower() for part in relative.parts}
    if path.is_symlink():
        raise ResourceBuildError(f"resource symlinks are not allowed: {relative}")
    if lowered_parts & FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
        raise ResourceBuildError(f"secret-like package resource is forbidden: {relative}")
    if path.name not in ALLOWED_SPECIAL_NAMES and path.suffix.lower() not in ALLOWED_SUFFIXES:
        raise ResourceBuildError(
            f"unsupported package resource type: {relative}; review and allow it explicitly"
        )


def iter_package_resources(source_root: Path) -> tuple[Path, ...]:
    """Return the reviewed resource files that may enter the distribution."""
    source_root = source_root.resolve()
    resources: list[Path] = []
    for directory in RESOURCE_DIRS:
        resource_root = source_root / directory
        if not resource_root.is_dir():
            raise ResourceBuildError(f"required resource directory is missing: {directory}")
        for path in sorted(resource_root.rglob("*")):
            if _is_ignored(path):
                continue
            if path.is_symlink():
                raise ResourceBuildError(
                    f"resource symlinks are not allowed: {path.relative_to(source_root)}"
                )
            if not path.is_file():
                continue
            _validate_resource(path, source_root)
            resources.append(path)
    if not resources:
        raise ResourceBuildError("no package resources were found")
    return tuple(resources)


def copy_package_resources(source_root: Path, package_root: Path) -> tuple[Path, ...]:
    """Copy reviewed resources into a wheel build's package directory."""
    source_root = source_root.resolve()
    package_root = package_root.resolve()
    resources = iter_package_resources(source_root)

    for directory in RESOURCE_DIRS:
        target_root = package_root / directory
        if target_root.is_symlink() or (target_root.exists() and not target_root.is_dir()):
            target_root.unlink()
        elif target_root.is_dir():
            shutil.rmtree(target_root)

    copied: list[Path] = []
    for source in resources:
        relative = source.relative_to(source_root)
        target = package_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append(target)
    return tuple(copied)
