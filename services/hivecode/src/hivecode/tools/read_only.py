"""Read-only tools for agents.

All tools validate paths against the scope policy before execution.
No tool can modify files or execute arbitrary commands.
"""

import ast
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from hivecode.policy.scope import ScopeConfig, is_path_allowed


@dataclass
class ToolResult:
    """Result of a tool call."""

    success: bool
    content: str
    error: str | None = None


class ReadOnlyTools:
    """Read-only tools for repository inspection.

    All tools enforce scope policy — paths outside the allowed scope
    are rejected.
    """

    def __init__(self, workspace_path: str, scope: ScopeConfig):
        self.workspace = Path(workspace_path)
        self.scope = scope

    def read_file(self, path: str, start_line: int = 1, end_line: int | None = None) -> ToolResult:
        """Read a file from the workspace.

        Args:
            path: Relative path within the workspace
            start_line: First line to read (1-indexed)
            end_line: Last line to read (None = end of file)
        """
        if not is_path_allowed(path, self.scope):
            return ToolResult(success=False, content="", error=f"Path '{path}' is outside allowed scope")

        file_path = self.workspace / path
        if not file_path.exists():
            return ToolResult(success=False, content="", error=f"File not found: {path}")

        if not file_path.is_file():
            return ToolResult(success=False, content="", error=f"Not a file: {path}")

        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
            end = end_line if end_line is not None else len(lines)
            selected = lines[start_line - 1 : end]

            # Truncate large files
            max_lines = 500
            truncated = False
            if len(selected) > max_lines:
                selected = selected[:max_lines]
                truncated = True

            content = "\n".join(selected)
            if truncated:
                content += f"\n\n... (truncated, showing {max_lines} of {end - start_line + 1} lines)"

            return ToolResult(success=True, content=content)
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))

    def search(self, pattern: str, path: str = ".", file_pattern: str = "*.py") -> ToolResult:
        """Search for a pattern in the workspace using ripgrep.

        Args:
            pattern: Search pattern (regex)
            path: Subdirectory to search in
            file_pattern: File glob pattern
        """
        if not is_path_allowed(path, self.scope):
            return ToolResult(success=False, content="", error=f"Path '{path}' is outside allowed scope")

        search_path = self.workspace / path
        if not search_path.exists():
            return ToolResult(success=False, content="", error=f"Path not found: {path}")

        try:
            result = subprocess.run(
                ["rg", "--json", "-e", pattern, "-g", file_pattern, str(search_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 1:  # No matches
                return ToolResult(success=True, content="No matches found")

            if result.returncode != 0:
                return ToolResult(success=False, content="", error=result.stderr)

            # Parse JSON output
            import json

            matches = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    data = json.loads(line)
                    if data.get("type") == "match":
                        match_data = data["data"]
                        matches.append(
                            f"{match_data['path']['text']}:{match_data['line_number']}: "
                            f"{match_data['lines']['text'].strip()}"
                        )

            # Limit results
            max_matches = 50
            truncated = len(matches) > max_matches
            matches = matches[:max_matches]

            output = "\n".join(matches)
            if truncated:
                output += f"\n\n... (truncated, showing {max_matches} of {len(matches)} matches)"

            return ToolResult(success=True, content=output)
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, content="", error="Search timed out")
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))

    def symbol_lookup(self, symbol_name: str, path: str = ".") -> ToolResult:
        """Look up a symbol (function, class) using Python AST.

        Args:
            symbol_name: Name of the symbol to find
            path: Subdirectory to search in
        """
        if not is_path_allowed(path, self.scope):
            return ToolResult(success=False, content="", error=f"Path '{path}' is outside allowed scope")

        search_path = self.workspace / path
        if not search_path.exists():
            return ToolResult(success=False, content="", error=f"Path not found: {path}")

        results = []
        for py_file in search_path.rglob("*.py"):
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        if node.name == symbol_name:
                            rel_path = py_file.relative_to(self.workspace)
                            results.append(
                                f"{rel_path}:{node.lineno}: {type(node).__name__} '{node.name}'"
                            )
            except (SyntaxError, UnicodeDecodeError):
                continue

        if not results:
            return ToolResult(success=True, content=f"Symbol '{symbol_name}' not found")

        return ToolResult(success=True, content="\n".join(results))

    def list_files(self, path: str = ".") -> ToolResult:
        """List files in a directory.

        Args:
            path: Relative directory path
        """
        if not is_path_allowed(path, self.scope):
            return ToolResult(success=False, content="", error=f"Path '{path}' is outside allowed scope")

        dir_path = self.workspace / path
        if not dir_path.exists():
            return ToolResult(success=False, content="", error=f"Path not found: {path}")

        if not dir_path.is_dir():
            return ToolResult(success=False, content="", error=f"Not a directory: {path}")

        try:
            entries = []
            for entry in sorted(dir_path.iterdir()):
                if entry.is_dir():
                    # Count files in directory
                    file_count = sum(1 for _ in entry.rglob("*") if _.is_file())
                    entries.append(f"[DIR]  {entry.name}/ ({file_count} files)")
                else:
                    size = entry.stat().st_size
                    entries.append(f"[FILE] {entry.name} ({size} bytes)")

            # Limit results
            max_entries = 100
            truncated = len(entries) > max_entries
            entries = entries[:max_entries]

            output = "\n".join(entries)
            if truncated:
                output += f"\n\n... (truncated, showing {max_entries} of {len(entries)} entries)"

            return ToolResult(success=True, content=output)
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))

    def get_file_info(self, path: str) -> ToolResult:
        """Get metadata about a file.

        Args:
            path: Relative file path
        """
        if not is_path_allowed(path, self.scope):
            return ToolResult(success=False, content="", error=f"Path '{path}' is outside allowed scope")

        file_path = self.workspace / path
        if not file_path.exists():
            return ToolResult(success=False, content="", error=f"File not found: {path}")

        try:
            stat = file_path.stat()
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            # Detect Python version
            python_version = "unknown"
            try:
                tree = ast.parse(content)
                # Check for Python 3.10+ syntax (match statements, | union types)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Match):
                        python_version = "3.10+"
                        break
            except SyntaxError:
                pass

            info = f"""File: {path}
Size: {stat.st_size} bytes
Lines: {len(lines)}
Python version: {python_version}
Modified: {stat.st_mtime}"""

            return ToolResult(success=True, content=info)
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))
