"""Filesystem sandbox.

All filesystem tools resolve user-supplied paths through :class:`FileSandbox`,
which confines access to a configured set of root directories and rejects
path-traversal attempts (``..``, symlinks, absolute escapes). If no roots are
configured, filesystem access is denied entirely - a deliberately safe default.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from app.config import Settings
from app.services.tools.base import ToolExecutionError, ToolPermissionError

# 1 MiB default cap for read/write operations.
_DEFAULT_MAX_FILE_BYTES = 1024 * 1024


class FileSandbox:
    """Confines filesystem access to an allow-list of resolved root directories."""

    def __init__(
        self, roots: Sequence[str | Path], *, max_file_bytes: int = _DEFAULT_MAX_FILE_BYTES
    ) -> None:
        self._roots: list[Path] = [Path(r).expanduser().resolve() for r in roots]
        self._max_file_bytes = max_file_bytes

    @property
    def roots(self) -> list[Path]:
        return list(self._roots)

    @property
    def max_file_bytes(self) -> int:
        return self._max_file_bytes

    def resolve(self, path: str) -> Path:
        """Resolve ``path`` and ensure it lies within an allowed root.

        Raises :class:`ToolPermissionError` if access is disabled or the path
        escapes the sandbox. Resolution normalises ``..`` and symlinks, so the
        check cannot be bypassed by traversal.
        """
        if not self._roots:
            raise ToolPermissionError(
                "Filesystem access is disabled: no sandbox roots are configured "
                "(set EXO_TOOL_FS_ALLOWED_ROOTS)."
            )
        # strict=False: the target need not exist yet (e.g. write/create).
        resolved = Path(path).expanduser().resolve()
        if any(self._is_within(resolved, root) for root in self._roots):
            return resolved
        raise ToolPermissionError(f"Path '{path}' is outside the allowed sandbox roots.")

    @staticmethod
    def _is_within(candidate: Path, root: Path) -> bool:
        return candidate == root or root in candidate.parents

    def ensure_size(self, num_bytes: int) -> None:
        """Raise :class:`ToolExecutionError` if ``num_bytes`` exceeds the cap."""
        if num_bytes > self._max_file_bytes:
            raise ToolExecutionError(
                f"Operation exceeds the maximum file size of {self._max_file_bytes} bytes."
            )

    @classmethod
    def from_settings(cls, settings: Settings) -> FileSandbox:
        return cls(settings.tool_fs_allowed_roots, max_file_bytes=settings.tool_max_file_bytes)
