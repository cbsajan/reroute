"""
REROUTE CLI - Command History & Undo System

Tracks CLI operations and provides rollback functionality.
"""

import json
import time
import uuid
import threading
import os
import stat
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from .utils import CLIError


@dataclass
class Operation:
    """Represents a single CLI operation that can be undone."""
    
    operation_id: str
    command: str
    timestamp: float
    files_created: List[str]
    files_modified: List[str]
    files_deleted: List[str]
    directories_created: List[str]
    metadata: Dict[str, Any]
    
    @classmethod
    def generate_id(cls) -> str:
        """Generate a unique operation ID."""
        return f"op_{uuid.uuid4().hex[:8]}_{int(time.time())}"


class CommandHistory:
    """Manages command history and rollback operations."""

    def __init__(self, history_file: Optional[Path] = None):
        self.history_file = history_file or Path.cwd() / ".reroute" / "history.json"
        self.history_file.parent.mkdir(exist_ok=True)
        self._lock = threading.Lock()
        self.operations: List[Operation] = []
        self.load_history()
    
    def load_history(self):
        """Load command history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.operations = [
                        Operation(**op_data) for op_data in data.get('operations', [])
                    ]
            except (json.JSONDecodeError, KeyError) as e:
                # History file corrupted, start fresh
                self.operations = []
        else:
            self.operations = []
    
    def save_history(self):
        """Save command history to file with atomic write and secure permissions."""
        data = {
            'operations': [asdict(op) for op in self.operations]
        }
        with self._lock:
            temp_file = self.history_file.with_suffix('.tmp')
            try:
                with open(temp_file, 'w') as f:
                    json.dump(data, f, indent=2)
                # Set secure permissions (0600 - read/write for owner only)
                try:
                    os.chmod(temp_file, stat.S_IRUSR | stat.S_IWUSR)
                except OSError:
                    # Permission setting failed, but continue with the operation
                    pass
                # Atomic move
                temp_file.replace(self.history_file)
                # Ensure final file also has secure permissions
                try:
                    os.chmod(self.history_file, stat.S_IRUSR | stat.S_IWUSR)
                except OSError:
                    pass
            except Exception:
                if temp_file.exists():
                    temp_file.unlink()
                raise
    
    def add_operation(self, operation: Operation):
        """Add a new operation to history."""
        self.operations.append(operation)
        # Keep only last 50 operations
        if len(self.operations) > 50:
            self.operations = self.operations[-50:]
        self.save_history()
    
    def get_last_operation(self) -> Optional[Operation]:
        """Get the most recent operation."""
        return self.operations[-1] if self.operations else None
    
    def get_operation(self, operation_id: str) -> Optional[Operation]:
        """Get a specific operation by ID."""
        for op in self.operations:
            if op.operation_id == operation_id:
                return op
        return None
    
    def list_operations(self, limit: int = 10) -> List[Operation]:
        """List recent operations."""
        return self.operations[-limit:] if self.operations else []
    
    def rollback_operation(self, operation: Operation) -> List[str]:
        """Rollback a specific operation with safety checks."""
        rollback_log = []
        project_root = Path.cwd()

        # Validate all paths first
        for file_path in operation.files_created + operation.files_modified:
            path = Path(file_path).resolve()
            if not str(path).startswith(str(project_root.resolve())):
                raise CLIError(
                    f"Cannot rollback: path {file_path} is outside project directory",
                    suggestion="Operation contains unsafe paths. Manual cleanup may be required.",
                    error_code="U003"
                )

        # Plan rollback first
        rollback_plan = []

        # Plan to delete files that were created
        for file_path in reversed(operation.files_created):
            path = Path(file_path)
            if path.exists():
                rollback_plan.append(('delete', file_path, path))

        # Plan to restore modified files
        for file_path in reversed(operation.files_modified):
            backup_path = Path(file_path + ".reroute_backup")
            if backup_path.exists():
                rollback_plan.append(('restore', file_path, Path(file_path), backup_path))

        # Execute rollback plan
        try:
            for step in rollback_plan:
                if step[0] == 'delete':
                    _, file_path, path = step
                    try:
                        path.unlink()
                        rollback_log.append(f"Deleted: {file_path}")
                    except (PermissionError, OSError) as e:
                        rollback_log.append(f"Failed to delete {file_path}: {e}")

                elif step[0] == 'restore':
                    _, file_path, current_path, backup_path = step
                    try:
                        backup_path.replace(current_path)
                        rollback_log.append(f"Restored: {file_path}")
                        # Remove backup after successful restore
                        if backup_path.exists():
                            backup_path.unlink()
                    except (PermissionError, OSError) as e:
                        rollback_log.append(f"Failed to restore {file_path}: {e}")

        finally:
            # Clean up empty directories
            for dir_path in reversed(operation.directories_created):
                path = Path(dir_path)
                if path.exists() and path.is_dir() and not any(path.iterdir()):
                    try:
                        path.rmdir()
                        rollback_log.append(f"Removed directory: {dir_path}")
                    except (PermissionError, OSError):
                        pass  # Directory might be non-empty or locked

            # Remove from history
            with self._lock:
                if operation in self.operations:
                    self.operations.remove(operation)
                    self.save_history()

        return rollback_log


# Global history instance
_history_instance = None


def get_history() -> CommandHistory:
    """Get the global command history instance."""
    global _history_instance
    if _history_instance is None:
        _history_instance = CommandHistory()
    return _history_instance


class OperationTracker:
    """Context manager to track CLI operations for undo functionality."""
    
    def __init__(self, command: str, metadata: Dict[str, Any] = None):
        self.command = command
        self.metadata = metadata or {}
        self.operation = Operation(
            operation_id=Operation.generate_id(),
            command=command,
            timestamp=time.time(),
            files_created=[],
            files_modified=[],
            files_deleted=[],
            directories_created=[],
            metadata=metadata
        )
    
    def __enter__(self):
        return self.operation
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # Only add to history if operation succeeded
            get_history().add_operation(self.operation)
        return False  # Don't suppress exceptions


def create_file_backup(file_path: Path):
    """Create a backup of a file before modification with secure permissions."""
    if not file_path.exists():
        return None

    backup_path = Path(str(file_path) + ".reroute_backup")

    # Validate path is within project
    project_root = Path.cwd()
    if not str(file_path.resolve()).startswith(str(project_root.resolve())):
        raise CLIError(
            f"Cannot backup file outside project: {file_path}",
            error_code="U004"
        )

    try:
        backup_path.write_bytes(file_path.read_bytes())
        # Set secure permissions (0600 - read/write for owner only)
        try:
            os.chmod(backup_path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            # Permission setting failed, but continue with the operation
            pass
        return backup_path
    except (PermissionError, OSError) as e:
        raise CLIError(
            f"Failed to create backup for {file_path}: {e}",
            suggestion="Check file permissions and disk space.",
            error_code="U005"
        )


def track_file_creation(operation: Operation, file_path: str):
    """Track that a file was created."""
    if file_path not in operation.files_created:
        operation.files_created.append(file_path)


def track_file_modification(operation: Operation, file_path: str):
    """Track that a file was modified (creates backup)."""
    path = Path(file_path)
    if path.exists():
        create_file_backup(path)
        if file_path not in operation.files_modified:
            operation.files_modified.append(file_path)


def track_directory_creation(operation: Operation, dir_path: str):
    """Track that a directory was created."""
    if dir_path not in operation.directories_created:
        operation.directories_created.append(dir_path)


__all__ = [
    "CommandHistory", "OperationTracker", "get_history",
    "create_file_backup", "track_file_creation",
    "track_file_modification", "track_directory_creation"
]
