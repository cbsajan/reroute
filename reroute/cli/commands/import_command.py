"""
OpenAPI import command for REROUTE CLI.

Implements the 'reroute import' command to generate routes from
OpenAPI specifications.
"""

import click
import os
import sys
from pathlib import Path
from typing import Optional

from reroute.openapi.parser import OpenAPIParser
from reroute.openapi.generator import RouteGenerator
from reroute.openapi.model_generator import ModelGenerator


def find_project_root() -> Path:
    """Find the project root directory.

    Looks for common project markers:
    - pyproject.toml
    - setup.py
    - config.py (REROUTE app marker)
    - app/ directory

    Returns:
        Path to project root directory
    """
    current = Path.cwd()

    # Project markers to look for (in priority order)
    markers = [
        "pyproject.toml",  # Modern Python project
        "setup.py",        # Legacy Python project
        "config.py",       # REROUTE app marker
        "app",             # REROUTE app directory
    ]

    # Walk up the directory tree
    for parent in [current] + list(current.parents):
        # Check if any marker exists
        for marker in markers:
            marker_path = parent / marker
            if marker_path.exists():
                return parent

    # If no markers found, use current directory
    return current


def detect_routes_dir(project_root: Path) -> str:
    """Detect the routes directory for the project.

    Args:
        project_root: Path to project root

    Returns:
        Relative path to routes directory from project root
    """
    # Try to import config and read ROUTES_DIR_NAME
    config_path = project_root / "config.py"
    if config_path.exists():
        # Add project root to sys.path temporarily
        original_path = sys.path.copy()
        try:
            sys.path.insert(0, str(project_root))

            # Try to import config
            import importlib.util
            spec = importlib.util.spec_from_file_location("config", config_path)
            if spec and spec.loader:
                config_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(config_module)

                # Look for AppConfig or Config class
                config_class = getattr(config_module, 'AppConfig', None)
                if not config_class:
                    config_class = getattr(config_module, 'Config', None)

                if config_class:
                    # Check if it has Internal class with ROUTES_DIR_NAME
                    if hasattr(config_class, 'Internal'):
                        routes_dir_name = config_class.Internal.ROUTES_DIR_NAME
                        # Return "app/routes" as default structure
                        return f"app/{routes_dir_name}"

                    # Check if it has ROUTES_DIR_NAME directly
                    if hasattr(config_class, 'ROUTES_DIR_NAME'):
                        routes_dir_name = config_class.ROUTES_DIR_NAME
                        return f"app/{routes_dir_name}"

        except ImportError:
            # Config file has import errors - use default
            pass
        except (AttributeError, TypeError):
            # Config file missing expected attributes - use default
            pass
        except Exception:
            # Log unexpected errors but continue with default
            pass
        finally:
            # Restore original sys.path
            sys.path = original_path

    # Default to app/routes
    return "app/routes"


@click.group()
def import_cmd():
    """Import APIs from OpenAPI specifications."""
    pass


@import_cmd.command()
@click.argument("spec_path", type=click.Path(exists=True))
@click.option(
    "--output-dir", "-o",
    type=click.Path(),
    default=None,
    help="Output directory for generated routes (default: auto-detected from project structure)",
)
@click.option(
    "--models-dir", "-m",
    type=click.Path(),
    default="app/models",
    help="Output directory for generated models",
)
@click.option(
    "--base-path", "-b",
    type=str,
    default="",
    help="Base path to strip from route paths",
)
@click.option(
    "--generate-tests", "-t",
    is_flag=True,
    help="Generate test files for routes",
)
@click.option(
    "--dry-run", "-d",
    is_flag=True,
    help="Show what would be generated without writing files",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed information",
)
def openapi(spec_path: str, output_dir: str, models_dir: str,
             base_path: str, generate_tests: bool, dry_run: bool,
             verbose: bool):
    """Import routes from an OpenAPI specification.

    \b
    Example:
        reroute import openapi openapi.yaml
        reroute import openapi swagger.json --output-dir api/routes
        reroute import openapi spec.yaml --generate-tests --base-path /api/v1
    """
    try:
        # Auto-detect project root and routes directory if not specified
        if output_dir is None:
            project_root = find_project_root()
            output_dir = detect_routes_dir(project_root)

            if verbose:
                click.echo(f"Auto-detected project root: {project_root}")
                click.echo(f"Using routes directory: {output_dir}")

        # Parse the OpenAPI specification
        click.echo(f"Parsing OpenAPI spec: {spec_path}")
        parser = OpenAPIParser(spec_path)
        spec = parser.parse_spec()

        if verbose:
            info = parser.get_info()
            click.echo(f"\nAPI: {info.get('title', 'Unknown')}")
            click.echo(f"Version: {info.get('version', 'Unknown')}")
            click.echo(f"Description: {info.get('description', 'N/A')}")

        # Extract operations and schemas
        operations = parser.extract_operations()
        schemas = parser.extract_schemas()

        click.echo(f"Found {len(operations)} operations")
        click.echo(f"Found {len(schemas)} schema definitions")

        # Get base path from spec if not provided
        if not base_path:
            base_path = parser.get_base_path()
            if base_path and verbose:
                click.echo(f"Using base path from spec: {base_path}")

        # Generate routes
        click.echo(f"\nGenerating routes in: {output_dir}")
        generator = RouteGenerator()
        output_path = Path(output_dir)

        if not dry_run:
            generated = generator.create_folder_structure(
                operations,
                output_path,
                base_path,
            )

            # Count generated files
            total_files = sum(len(files) for files in generated.values())
            click.echo(f"Generated {total_files} route files")

            for resource_path, files in generated.items():
                for file_path in files:
                    click.echo(f"  - {file_path}")
        else:
            click.echo("[DRY RUN] Would generate routes:")
            for op in operations[:5]:  # Show first 5
                click.echo(f"  - {op.method.upper()} {op.path}")
            if len(operations) > 5:
                click.echo(f"  ... and {len(operations) - 5} more")

        # Generate models
        if schemas:
            click.echo(f"\nGenerating models in: {models_dir}")
            model_gen = ModelGenerator()
            models_path = Path(models_dir)

            if not dry_run:
                models_file = models_path / "openapi.py"
                model_gen.generate_models_file(schemas, models_file)
                click.echo(f"  - {models_file}")
                click.echo(f"Generated {len(schemas)} model classes")
            else:
                click.echo("[DRY RUN] Would generate models:")
                for name in list(schemas.keys())[:5]:
                    click.echo(f"  - {name}")
                if len(schemas) > 5:
                    click.echo(f"  ... and {len(schemas) - 5} more")

        # Generate tests if requested
        if generate_tests and not dry_run:
            click.echo("\nGenerating test files...")
            test_output = Path("tests/routes")
            test_output.mkdir(parents=True, exist_ok=True)
            click.echo(f"Test files would be generated in: {test_output}")
            click.echo("Note: Test generation not yet implemented")

        click.echo("\nImport complete!")

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        raise click.Abort()


@import_cmd.command()
@click.argument("route_dir", type=click.Path(exists=True))
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="openapi.yaml",
    help="Output path for OpenAPI spec",
)
@click.option(
    "--format", "-f",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="Output format (yaml or json)",
)
@click.option(
    "--title", "-t",
    type=str,
    default="API",
    help="API title",
)
@click.option(
    "--version", "-v",
    type=str,
    default="1.0.0",
    help="API version",
)
def sync(route_dir: str, output: str, format: str, title: str, version: str):
    """Generate OpenAPI spec from existing REROUTE routes (reverse sync).

    \b
    Example:
        reroute import sync app/routes --output api-spec.yaml
        reroute import sync app/routes --format json --title "My API"
    """
    try:
        click.echo("Scanning routes...")
        route_path = Path(route_dir)

        # Find all route files
        route_files = list(route_path.rglob("page.py"))
        click.echo(f"Found {len(route_files)} route files")

        # Parse routes and build spec
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": title,
                "version": version,
            },
            "paths": {},
            "components": {
                "schemas": {},
            },
        }

        if format == "yaml":
            import yaml
            output_path = Path(output)
            output_path.write_text(yaml.dump(spec, default_flow_style=False))
        else:
            import json
            output_path = Path(output)
            output_path.write_text(json.dumps(spec, indent=2))

        click.echo(f"OpenAPI spec written to: {output}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


# Add the import command group to CLI
def register_import_command(cli):
    """Register import commands with CLI group.

    Args:
        cli: Click CLI group
    """
    cli.add_command(import_cmd, name="import")
