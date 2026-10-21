"""Wire sibling backend and create a single AppContainer for the GUI."""

from __future__ import annotations

import os
import sys
from pathlib import Path

FRONTEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BACKEND_ROOT = FRONTEND_ROOT.parent / "electronic-library-backend"


def ensure_backend_on_path(backend_root: Path | None = None) -> Path:
    root = Path(
        os.environ.get("LIBRARY_BACKEND_ROOT", "")
        or (backend_root or DEFAULT_BACKEND_ROOT)
    ).resolve()
    if not root.is_dir():
        raise RuntimeError(
            f"Backend not found at {root}. "
            "Set LIBRARY_BACKEND_ROOT or place electronic-library-backend next to this project."
        )
    root_str = str(root)
    if root_str in sys.path:
        sys.path.remove(root_str)
    sys.path.insert(0, root_str)
    return root


def init_app_container(data_dir: Path | str | None = None):
    """Initialize backend container once for the application lifetime."""
    backend_root = ensure_backend_on_path()
    from app.main import init_backend  # noqa: WPS433 — backend package

    if data_dir is None:
        env_data = os.environ.get("LIBRARY_DATA_DIR")
        data_dir = Path(env_data) if env_data else backend_root / "data"
    return init_backend(data_dir)
