"""Filesystem tools.

Every tool resolves paths through a shared :class:`FileSandbox`, so all access
is confined to the configured roots and protected from path traversal. Blocking
I/O runs in a worker thread. Destructive operations (write, move, delete)
declare ``requires_confirmation = True`` and the write permission.
"""

from __future__ import annotations

import asyncio
import shutil
from typing import Any

from pydantic import BaseModel, Field

from app.services.tools.base import (
    BaseTool,
    Permission,
    ToolContext,
    ToolExecutionError,
)
from app.services.tools.sandbox import FileSandbox


class _SandboxedTool:
    """Mixin holding the shared sandbox for filesystem tools."""

    def __init__(self, sandbox: FileSandbox) -> None:
        self._sandbox = sandbox


# --- read -------------------------------------------------------------------


class ReadFileParams(BaseModel):
    path: str = Field(min_length=1, description="Path to the file to read")


class ReadFileTool(_SandboxedTool, BaseTool[ReadFileParams]):
    name = "read_file"
    description = "Read the UTF-8 text contents of a file within the sandbox."
    permissions = frozenset({Permission.FILESYSTEM_READ})
    params_model = ReadFileParams

    async def run(self, params: ReadFileParams, context: ToolContext) -> dict[str, Any]:
        path = self._sandbox.resolve(params.path)

        def _read() -> str:
            if not path.is_file():
                raise ToolExecutionError(f"Not a file: '{params.path}'.")
            self._sandbox.ensure_size(path.stat().st_size)
            try:
                return path.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                raise ToolExecutionError("File is not valid UTF-8 text.") from exc

        content = await asyncio.to_thread(_read)
        return {"path": str(path), "content": content, "bytes": len(content.encode("utf-8"))}


# --- write ------------------------------------------------------------------


class WriteFileParams(BaseModel):
    path: str = Field(min_length=1, description="Path to the file to write")
    content: str = Field(description="Text content to write")
    append: bool = Field(default=False, description="Append instead of overwriting")


class WriteFileTool(_SandboxedTool, BaseTool[WriteFileParams]):
    name = "write_file"
    description = "Write UTF-8 text to a file within the sandbox (creates parent directories)."
    permissions = frozenset({Permission.FILESYSTEM_WRITE})
    requires_confirmation = True
    params_model = WriteFileParams

    async def run(self, params: WriteFileParams, context: ToolContext) -> dict[str, Any]:
        path = self._sandbox.resolve(params.path)
        data = params.content.encode("utf-8")
        self._sandbox.ensure_size(len(data))

        def _write() -> int:
            path.parent.mkdir(parents=True, exist_ok=True)
            mode = "a" if params.append else "w"
            with path.open(mode, encoding="utf-8") as handle:
                return handle.write(params.content)

        written = await asyncio.to_thread(_write)
        return {"path": str(path), "written_chars": written, "appended": params.append}


# --- list -------------------------------------------------------------------


class ListDirectoryParams(BaseModel):
    path: str = Field(min_length=1, description="Directory to list")
    include_hidden: bool = Field(default=False, description="Include dot-prefixed entries")


class ListDirectoryTool(_SandboxedTool, BaseTool[ListDirectoryParams]):
    name = "list_directory"
    description = "List the entries of a directory within the sandbox."
    permissions = frozenset({Permission.FILESYSTEM_READ})
    params_model = ListDirectoryParams

    async def run(self, params: ListDirectoryParams, context: ToolContext) -> dict[str, Any]:
        path = self._sandbox.resolve(params.path)

        def _list() -> list[dict[str, Any]]:
            if not path.is_dir():
                raise ToolExecutionError(f"Not a directory: '{params.path}'.")
            entries: list[dict[str, Any]] = []
            for entry in sorted(path.iterdir(), key=lambda p: p.name):
                if not params.include_hidden and entry.name.startswith("."):
                    continue
                is_dir = entry.is_dir()
                entries.append(
                    {
                        "name": entry.name,
                        "type": "directory" if is_dir else "file",
                        "size": None if is_dir else entry.stat().st_size,
                    }
                )
            return entries

        entries = await asyncio.to_thread(_list)
        return {"path": str(path), "entries": entries, "count": len(entries)}


# --- search -----------------------------------------------------------------


class SearchFilesParams(BaseModel):
    path: str = Field(min_length=1, description="Root directory to search")
    pattern: str = Field(default="*", description="Glob pattern (e.g. '*.py')")
    max_results: int = Field(default=100, ge=1, le=1000)


class SearchFilesTool(_SandboxedTool, BaseTool[SearchFilesParams]):
    name = "search_files"
    description = "Recursively find files matching a glob pattern within the sandbox."
    permissions = frozenset({Permission.FILESYSTEM_READ})
    params_model = SearchFilesParams

    async def run(self, params: SearchFilesParams, context: ToolContext) -> dict[str, Any]:
        root = self._sandbox.resolve(params.path)

        def _search() -> tuple[list[str], bool]:
            if not root.is_dir():
                raise ToolExecutionError(f"Not a directory: '{params.path}'.")
            matches: list[str] = []
            truncated = False
            for match in root.rglob(params.pattern):
                if len(matches) >= params.max_results:
                    truncated = True
                    break
                matches.append(str(match.relative_to(root)))
            return matches, truncated

        matches, truncated = await asyncio.to_thread(_search)
        return {
            "path": str(root),
            "pattern": params.pattern,
            "matches": matches,
            "count": len(matches),
            "truncated": truncated,
        }


# --- create folder ----------------------------------------------------------


class CreateFolderParams(BaseModel):
    path: str = Field(min_length=1, description="Directory to create")
    parents: bool = Field(default=True, description="Create missing parent directories")


class CreateFolderTool(_SandboxedTool, BaseTool[CreateFolderParams]):
    name = "create_folder"
    description = "Create a new directory within the sandbox."
    permissions = frozenset({Permission.FILESYSTEM_WRITE})
    params_model = CreateFolderParams

    async def run(self, params: CreateFolderParams, context: ToolContext) -> dict[str, Any]:
        path = self._sandbox.resolve(params.path)

        def _mkdir() -> None:
            try:
                path.mkdir(parents=params.parents, exist_ok=False)
            except FileExistsError as exc:
                raise ToolExecutionError(f"Already exists: '{params.path}'.") from exc
            except FileNotFoundError as exc:
                raise ToolExecutionError(
                    f"Parent directory does not exist for '{params.path}'."
                ) from exc

        await asyncio.to_thread(_mkdir)
        return {"path": str(path), "created": True}


# --- move -------------------------------------------------------------------


class MoveFilesParams(BaseModel):
    source: str = Field(min_length=1, description="Path to move from")
    destination: str = Field(min_length=1, description="Path to move to")


class MoveFilesTool(_SandboxedTool, BaseTool[MoveFilesParams]):
    name = "move_files"
    description = "Move or rename a file or directory within the sandbox."
    permissions = frozenset({Permission.FILESYSTEM_WRITE})
    requires_confirmation = True
    params_model = MoveFilesParams

    async def run(self, params: MoveFilesParams, context: ToolContext) -> dict[str, Any]:
        source = self._sandbox.resolve(params.source)
        destination = self._sandbox.resolve(params.destination)

        def _move() -> None:
            if not source.exists():
                raise ToolExecutionError(f"Source does not exist: '{params.source}'.")
            if destination.exists():
                raise ToolExecutionError(f"Destination already exists: '{params.destination}'.")
            shutil.move(str(source), str(destination))

        await asyncio.to_thread(_move)
        return {"source": str(source), "destination": str(destination), "moved": True}


# --- delete -----------------------------------------------------------------


class DeleteFilesParams(BaseModel):
    path: str = Field(min_length=1, description="Path to delete")
    recursive: bool = Field(default=False, description="Delete a non-empty directory recursively")


class DeleteFilesTool(_SandboxedTool, BaseTool[DeleteFilesParams]):
    name = "delete_files"
    description = "Delete a file or directory within the sandbox (irreversible)."
    permissions = frozenset({Permission.FILESYSTEM_WRITE})
    requires_confirmation = True
    params_model = DeleteFilesParams

    async def run(self, params: DeleteFilesParams, context: ToolContext) -> dict[str, Any]:
        path = self._sandbox.resolve(params.path)

        def _delete() -> str:
            if not path.exists():
                raise ToolExecutionError(f"Path does not exist: '{params.path}'.")
            if path.is_dir():
                if params.recursive:
                    shutil.rmtree(path)
                else:
                    try:
                        path.rmdir()
                    except OSError as exc:
                        raise ToolExecutionError(
                            "Directory is not empty; set recursive=true to delete it."
                        ) from exc
                return "directory"
            path.unlink()
            return "file"

        kind = await asyncio.to_thread(_delete)
        return {"path": str(path), "deleted": kind}
