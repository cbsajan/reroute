"""
REROUTE CLI - Utilities

Progress indicators and improved error handling for CLI commands.
"""

import click
import sys
import time
from contextlib import contextmanager
from typing import Optional, Callable, Any


# Progress indicator characters (no emojis per user preference)
SPINNER_CHARS = ['|', '/', '-', '\\']


class ProgressIndicator:
    """
    Simple progress indicator for CLI operations.

    Usage:
        with ProgressIndicator("Creating files") as progress:
            for item in items:
                progress.update(f"Processing {item}")
                do_work(item)
    """

    def __init__(self, message: str, show_spinner: bool = True):
        self.message = message
        self.show_spinner = show_spinner
        self.current_step = 0
        self.total_steps = 0
        self.spinner_idx = 0

    def __enter__(self):
        if self.show_spinner:
            click.secho(f"[....] {self.message}", fg='blue', nl=False)
        else:
            click.secho(f"[....] {self.message}", fg='blue')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # Success - overwrite with checkmark
            click.echo('\r', nl=False)
            click.secho(f"[ OK ] {self.message}", fg='green')
        else:
            # Error - overwrite with error indicator
            click.echo('\r', nl=False)
            click.secho(f"[FAIL] {self.message}", fg='red')
        return False  # Don't suppress exceptions

    def update(self, sub_message: str = None):
        """Update the progress message."""
        if sub_message:
            click.echo('\r' + ' ' * 80 + '\r', nl=False)
            spinner = SPINNER_CHARS[self.spinner_idx % len(SPINNER_CHARS)]
            click.secho(f"[ {spinner}  ] {self.message}: {sub_message}", fg='blue', nl=False)
            self.spinner_idx += 1


@contextmanager
def progress_step(message: str):
    """
    Context manager for a single progress step.

    Usage:
        with progress_step("Creating config.py"):
            create_config_file()
    """
    click.secho(f"  [....] {message}", fg='blue', nl=False)
    try:
        yield
        click.echo('\r', nl=False)
        click.secho(f"  [ OK ] {message}", fg='green')
    except Exception:
        click.echo('\r', nl=False)
        click.secho(f"  [FAIL] {message}", fg='red')
        raise


def progress_steps(steps: list):
    """
    Execute a list of steps with progress indicators.

    Args:
        steps: List of tuples (message, callable)

    Usage:
        progress_steps([
            ("Creating directory", lambda: os.makedirs("foo")),
            ("Writing config", lambda: write_file("config.py")),
        ])
    """
    for message, func in steps:
        with progress_step(message):
            func()


class CLIError(Exception):
    """
    Custom exception for CLI errors with actionable suggestions.

    Attributes:
        message: Error message
        suggestion: Actionable suggestion for the user
        error_code: Optional error code for documentation reference
    """

    def __init__(self, message: str, suggestion: str = None, error_code: str = None):
        self.message = message
        self.suggestion = suggestion
        self.error_code = error_code
        super().__init__(message)


def handle_error(error: Exception, context: str = None):
    """
    Handle errors with improved formatting and suggestions.

    Args:
        error: The exception that occurred
        context: Optional context about what operation failed
    """
    click.echo()

    if isinstance(error, CLIError):
        # Custom error with suggestion
        if error.error_code:
            click.secho(f"[ERROR {error.error_code}] ", fg='red', bold=True, nl=False)
        else:
            click.secho("[ERROR] ", fg='red', bold=True, nl=False)

        click.secho(error.message, fg='red')

        if error.suggestion:
            click.secho("\n[TIP] ", fg='yellow', bold=True, nl=False)
            click.secho(error.suggestion, fg='yellow')

    elif isinstance(error, FileNotFoundError):
        click.secho("[ERROR] ", fg='red', bold=True, nl=False)
        click.secho(f"File not found: {error.filename or error}", fg='red')
        click.secho("\n[TIP] ", fg='yellow', bold=True, nl=False)
        click.secho("Check that the file path is correct and the file exists.", fg='yellow')

    elif isinstance(error, PermissionError):
        click.secho("[ERROR] ", fg='red', bold=True, nl=False)
        click.secho(f"Permission denied: {error.filename or error}", fg='red')
        click.secho("\n[TIP] ", fg='yellow', bold=True, nl=False)
        click.secho("Check file permissions or run with appropriate privileges.", fg='yellow')

    elif isinstance(error, ImportError):
        module_name = str(error).replace("No module named ", "").replace("'", "")
        click.secho("[ERROR] ", fg='red', bold=True, nl=False)
        click.secho(f"Missing dependency: {module_name}", fg='red')
        click.secho("\n[TIP] ", fg='yellow', bold=True, nl=False)
        click.secho(f"Install with: pip install {module_name}", fg='cyan')

    else:
        # Generic error
        click.secho("[ERROR] ", fg='red', bold=True, nl=False)
        if context:
            click.secho(f"{context}: {error}", fg='red')
        else:
            click.secho(str(error), fg='red')

    click.echo()


def require_reroute_project():
    """
    Check if current directory is a REROUTE project.
    Raises CLIError with helpful suggestion if not.
    """
    from pathlib import Path

    app_routes = Path.cwd() / "app" / "routes"
    pyproject = Path.cwd() / "pyproject.toml"

    if not app_routes.exists():
        raise CLIError(
            "Not in a REROUTE project directory",
            suggestion="Run 'reroute init <project-name>' to create a new project, "
                      "or 'cd' into an existing REROUTE project.",
            error_code="E001"
        )

    # Check if it's actually a REROUTE project (has marker in pyproject.toml)
    if pyproject.exists():
        content = pyproject.read_text()
        if "reroute" not in content.lower():
            raise CLIError(
                "This appears to be a Python project but not a REROUTE project",
                suggestion="Ensure this project was created with 'reroute init' "
                          "or manually add REROUTE to dependencies.",
                error_code="E002"
            )


def require_database_setup():
    """
    Check if database is configured.
    Raises CLIError with helpful suggestion if not.
    """
    from pathlib import Path

    database_py = Path.cwd() / "app" / "database.py"
    migrations_dir = Path.cwd() / "migrations"

    if not database_py.exists():
        raise CLIError(
            "Database not configured in this project",
            suggestion="Initialize project with database: 'reroute init myapp --database postgres'\n"
                      "  Or manually create app/database.py with your database configuration.",
            error_code="E010"
        )

    if not migrations_dir.exists():
        raise CLIError(
            "Migrations not initialized",
            suggestion="Run 'reroute db init' to initialize database migrations.",
            error_code="E011"
        )


def confirm_destructive_action(message: str) -> bool:
    """
    Confirm a destructive action with the user.

    Args:
        message: Description of the destructive action

    Returns:
        True if user confirms, False otherwise
    """
    click.secho("\n[WARNING] ", fg='yellow', bold=True, nl=False)
    click.secho(message, fg='yellow')

    return click.confirm("Are you sure you want to proceed?", default=False)


def success_message(message: str, details: dict = None):
    """
    Display a success message with optional details.

    Args:
        message: Main success message
        details: Optional dict of key-value details to display
    """
    click.echo()
    click.secho("=" * 50, fg='green', bold=True)
    click.secho(f"[SUCCESS] {message}", fg='green', bold=True)
    click.secho("=" * 50, fg='green', bold=True)

    if details:
        click.echo()
        for key, value in details.items():
            click.secho(f"  {key}: ", fg='blue', nl=False)
            click.secho(str(value), fg='cyan')

    click.echo()


def info_box(title: str, lines: list):
    """
    Display an information box.

    Args:
        title: Box title
        lines: List of lines to display
    """
    width = max(len(title) + 4, max(len(line) for line in lines) + 4)

    click.secho("+" + "-" * (width - 2) + "+", fg='cyan')
    click.secho(f"| {title.center(width - 4)} |", fg='cyan', bold=True)
    click.secho("+" + "-" * (width - 2) + "+", fg='cyan')

    for line in lines:
        click.secho(f"| {line.ljust(width - 4)} |", fg='white')

    click.secho("+" + "-" * (width - 2) + "+", fg='cyan')


def next_steps(steps: list, title: str = "Next Steps"):
    """
    Display next steps for the user.

    Args:
        steps: List of step strings
        title: Section title
    """
    click.echo()
    click.secho(f"{title}:", fg='yellow', bold=True)

    for i, step in enumerate(steps, 1):
        click.secho(f"  {i}. ", fg='yellow', nl=False)
        click.secho(step, fg='cyan')

    click.echo()
