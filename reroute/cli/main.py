"""
REROUTE CLI Commands

Interactive CLI for REROUTE project scaffolding and code generation.
"""

import click
from pathlib import Path

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from click import Group

from reroute.cli.commands.db_commands import db  # type: ignore
from reroute.cli.commands.init_command import init
from reroute.cli.commands.create_command import generate, create
from reroute.cli.commands.helpers import is_reroute_project
from reroute.cli.update_checker import check_for_updates


def _version_callback(ctx, param, value):
    """Display version and check for updates."""
    if value:
        from reroute import __version__
        click.echo(f'REROUTE CLI v{__version__}')

        # Check for updates
        check_for_updates(__version__)

        ctx.exit()


@click.group()
@click.option('--version', '-V', is_flag=True, callback=_version_callback, expose_value=False, is_eager=True, help='Show version and exit')
@click.pass_context
def cli(ctx):
    """
    REROUTE CLI - File-based routing for Python backends

    Interactive project scaffolding and code generation.

    """
    # Check for updates (non-blocking, silent on errors)
    if ctx.invoked_subcommand and ctx.invoked_subcommand not in ['--version', '-V']:
        from reroute import __version__
        check_for_updates(__version__)

# Register all command groups
cli.add_command(db)  # type: ignore
cli.add_command(init) # type: ignore
cli.add_command(generate) # type: ignore
cli.add_command(create) # type: ignore


# TODO: Implement/use later
# @cli.command()
# def info():
#     """
#     Show REROUTE project information.
#
#     Displays:
#     - Project structure
#     - Route count
#     - Configuration details
#     - REROUTE version
#     """
#     from reroute import __version__
#
#     # Check if we're in a REROUTE project
#     if not is_reroute_project():
#         click.secho("[WARNING] Not in a REROUTE project directory", fg='yellow', bold=True)
#         click.secho("Run 'reroute init' to create a new project.\n", fg='yellow')
#
#         # Still show REROUTE version
#         click.secho(f"REROUTE Version: ", fg='blue', nl=False)
#         click.secho(__version__, fg='green', bold=True)
#         print()
#         return
#
#     # Get project info
#     cwd = Path.cwd()
#     routes_dir = cwd / "app" / "routes"
#
#     # Count routes
#     route_count = 0
#     route_files = []
#     if routes_dir.exists():
#         for route_file in routes_dir.rglob("page.py"):
#             route_count += 1
#             rel_path = route_file.relative_to(routes_dir.parent)
#             route_files.append(str(rel_path))
#
#     # Show project details
#     click.secho(f"Project Directory: ", fg='blue', nl=False)
#     click.secho(str(cwd.name), fg='green', bold=True)
#
#     click.secho(f"REROUTE Version: ", fg='blue', nl=False)
#     click.secho(__version__, fg='green', bold=True)
#
#     click.secho(f"Total Routes: ", fg='blue', nl=False)
#     click.secho(str(route_count), fg='green', bold=True)
#
#     # Show route structure
#     if route_count > 0:
#         click.secho("\nRoute Files:", fg='blue', bold=True)
#         for route_file in sorted(route_files):
#             click.secho(f"  - {route_file}", fg='green')
#
#     # Check for main files
#     main_files = []
#     for filename in ['main.py', 'app.py', 'server.py']:
#         if (cwd / filename).exists():
#             main_files.append(filename)
#
#     if main_files:
#         click.secho(f"\nMain Files: ", fg='blue', nl=False)
#         click.secho(", ".join(main_files), fg='green')
#
#     # Check for tests
#     tests_dir = cwd / "tests"
#     test_count = 0
#     if tests_dir.exists():
#         test_count = len(list(tests_dir.rglob("*.http"))) + len(list(tests_dir.rglob("test_*.py")))
#
#     if test_count > 0:
#         click.secho(f"Test Files: ", fg='blue', nl=False)
#         click.secho(str(test_count), fg='green')
#
#     print()


if __name__ == '__main__':
    cli()
