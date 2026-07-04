"""Path resolution that works both in editable installs and in wheels."""

from __future__ import annotations

from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent

# A source checkout has the canonical scripts beside this package. An installed
# wheel has its reviewed resources inside the package directory instead.
_SOURCE_ROOT = _PACKAGE_DIR.parent
IS_SOURCE_CHECKOUT = (
    (_SOURCE_ROOT / "scripts" / "validate_repo.py").is_file()
    and (_SOURCE_ROOT / "config" / "arc_testnet.facts.json").is_file()
)
REPO_ROOT = _SOURCE_ROOT if IS_SOURCE_CHECKOUT else _PACKAGE_DIR
DEFAULT_OUTPUT_ROOT = REPO_ROOT if IS_SOURCE_CHECKOUT else Path.cwd().resolve()


def _resolve_resource_dir(name: str) -> Path:
    """Find a resource directory in installed wheel or editable/development layout.

    In a built wheel, resources live next to this module under arc_builder_kit/.
    In a clone/editable install, resources live in the repository root, one level
    above this package.
    """
    installed = _PACKAGE_DIR / name
    if installed.exists() and installed.is_dir():
        return installed
    dev = _SOURCE_ROOT / name
    if dev.exists() and dev.is_dir():
        return dev
    raise FileNotFoundError(
        f"Could not locate {name!r} directory. "
        f"Tried {installed} and {dev}."
    )


PACKAGE_DIR = _PACKAGE_DIR
TEMPLATES_DIR = _resolve_resource_dir("templates")
CONFIG_DIR = _resolve_resource_dir("config")
EXAMPLES_DIR = _resolve_resource_dir("examples")

# Other scripts live in the repo scripts/ directory. In a wheel they are not
# shipped as standalone subprocess targets; the CLI/MCP tools import their
# functions directly.
SCRIPTS_DIR = REPO_ROOT / "scripts"
