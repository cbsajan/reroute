"""
REROUTE CLI - Undo Commands

Provides rollback functionality for CLI operations.
"""

import click
from pathlib import Path
from ..history import get_history, OperationTracker, CLIError
from ..utils import progress_step, success_message, next_steps


@click.command()
@click.option('--list', 'list_ops', is_flag=True, help='List recent operations')
@click.option('--operation-id', '-op', help='Specific operation ID to undo')
@click.option('--force', is_flag=True, help='Skip confirmation prompts')
@click.option('--limit', default=10, help='Number of operations to list (default: 10)')
def undo(list_ops, operation_id, force, limit):
    """
    Undo recent REROUTE CLI operations.
    
    Examples:
        reroute undo --list                    # List recent operations
        reroute undo                            # Undo last operation
        reroute undo --operation-id op_12345    # Undo specific operation
        reroute undo --force                    # Undo last without confirmation
    """
    history = get_history()
    
    if list_ops:
        _list_operations(history, limit)
        return
    
    # Determine which operation to undo
    if operation_id:
        operation = history.get_operation(operation_id)
        if not operation:
            raise CLIError(
                f"Operation '{operation_id}' not found",
                suggestion="Run 'reroute undo --list' to see available operations.",
                error_code="U001"
            )
    else:
        operation = history.get_last_operation()
        if not operation:
            click.secho("[INFO] No operations to undo.", fg='yellow')
            return
    
    # Show operation details
    _show_operation_details(operation)
    
    # Confirm undo
    if not force:
        click.echo()
        if not click.confirm(f"Do you want to undo this operation?", default=False):
            click.secho("[CANCELLED] Operation not undone.", fg='yellow')
            return
    
    # Perform rollback
    with progress_step("Rolling back operation"):
        try:
            rollback_log = history.rollback_operation(operation)
            
            success_message(
                f"Successfully rolled back: {operation.command}",
                {
                    "Operation ID": operation.operation_id,
                    "Files affected": len(rollback_log)
                }
            )
            
            if rollback_log:
                click.secho("Rollback details:", fg='blue', bold=True)
                for item in rollback_log:
                    click.secho(f"  - {item}", fg='cyan')
            
        except Exception as e:
            raise CLIError(
                f"Failed to rollback operation: {e}",
                suggestion="Some files may have been partially rolled back. "
                          "Check the project directory and manually clean up if needed.",
                error_code="U002"
            )


def _list_operations(history, limit):
    """List recent operations."""
    operations = history.list_operations(limit)
    
    if not operations:
        click.secho("[INFO] No operations in history.", fg='yellow')
        return
    
    click.secho("\nRecent Operations:", fg='blue', bold=True)
    click.secho("=" * 60, fg='blue')
    
    for i, op in enumerate(reversed(operations), 1):
        timestamp_str = _format_timestamp(op.timestamp)
        
        click.secho(f"{i:2d}. {op.operation_id}", fg='green', bold=True, nl=False)
        click.secho(f" - {op.command}", fg='white')
        click.secho(f"    {timestamp_str}", fg='cyan')
        
        # Show affected files count
        affected_count = len(op.files_created) + len(op.files_modified) + len(op.files_deleted)
        if affected_count > 0:
            click.secho(f"    Files affected: {affected_count}", fg='yellow')
        
        click.echo()
    
    click.secho(f"Showing {len(operations)} most recent operations.", fg='yellow')
    click.secho("Use 'reroute undo --operation-id <ID>' to undo a specific operation.", fg='cyan')


def _show_operation_details(operation):
    """Show detailed information about an operation."""
    click.secho("\nOperation Details:", fg='blue', bold=True)
    click.secho("=" * 40, fg='blue')
    
    click.secho(f"ID: ", fg='blue', nl=False)
    click.secho(operation.operation_id, fg='green', bold=True)
    
    click.secho(f"Command: ", fg='blue', nl=False)
    click.secho(operation.command, fg='white')
    
    click.secho(f"Time: ", fg='blue', nl=False)
    click.secho(_format_timestamp(operation.timestamp), fg='cyan')
    
    if operation.files_created:
        click.secho(f"\nFiles Created ({len(operation.files_created)}):", fg='yellow')
        for file_path in operation.files_created:
            click.secho(f"  + {file_path}", fg='green')
    
    if operation.files_modified:
        click.secho(f"\nFiles Modified ({len(operation.files_modified)}):", fg='yellow')
        for file_path in operation.files_modified:
            click.secho(f"  ~ {file_path}", fg='blue')
    
    if operation.files_deleted:
        click.secho(f"\nFiles Deleted ({len(operation.files_deleted)}):", fg='yellow')
        for file_path in operation.files_deleted:
            click.secho(f"  - {file_path}", fg='red')
    
    if operation.directories_created:
        click.secho(f"\nDirectories Created ({len(operation.directories_created)}):", fg='yellow')
        for dir_path in operation.directories_created:
            click.secho(f"  + {dir_path}/", fg='green')
    
    if operation.metadata:
        click.secho("\nMetadata:", fg='yellow')
        for key, value in operation.metadata.items():
            click.secho(f"  {key}: {value}", fg='cyan')


def _format_timestamp(timestamp):
    """Format timestamp for display."""
    import datetime
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")
