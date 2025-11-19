"""
REROUTE CLI Commands

Interactive CLI for REROUTE project scaffolding and code generation.
"""

import click
import questionary
from questionary import Style
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os
import sys


# Custom style for questionary prompts
custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),          # Question mark
    ('question', 'bold'),                   # Question text
    ('answer', 'fg:#2196f3 bold'),         # Selected answer
    ('pointer', 'fg:#673ab7 bold'),        # Selection pointer
    ('highlighted', 'fg:#2196f3 bold'),    # Highlighted choice
    ('selected', 'fg:#4caf50 bold'),       # Selected choice
    ('separator', 'fg:#cc5454'),           # Separator
    ('instruction', ''),                    # Instructions
    ('text', ''),                           # Plain text
    ('disabled', 'fg:#858585 italic')      # Disabled choices
])


# Setup Jinja2 environment
TEMPLATES_DIR = Path(__file__).parent / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True
)


@click.group()
def cli():
    """
    REROUTE CLI - File-based routing for Python backends

    Interactive project scaffolding and code generation.
    """
    # Display banner
    click.secho("\n" + "="*50, fg='cyan', bold=True)
    click.secho("  REROUTE CLI", fg='cyan', bold=True)
    click.secho("  File-based routing for Python backends", fg='cyan')
    click.secho("="*50 + "\n", fg='cyan', bold=True)


@cli.command()
@click.argument('name', required=False)
@click.option('--framework', default=None,
              type=click.Choice(['fastapi', 'flask'], case_sensitive=False),
              help='Backend framework (fastapi or flask)')
@click.option('--config',
              type=click.Choice(['dev', 'prod'], case_sensitive=False),
              default='dev',
              help='Configuration type (dev or prod)')
@click.option('--host', default='0.0.0.0', help='Server host')
@click.option('--port', default=7376, type=int, help='Server port')
@click.option('--description', default='', help='Project description')
def init(name, framework, config, host, port, description):
    """
    Initialize a new REROUTE project.

    Creates project structure with:
    - app/routes/ directory for file-based routing
    - Main application file (FastAPI/Flask)
    - Configuration files
    - Example route

    Examples:
        reroute init
        reroute init  myapi --framework fastapi
    """
    click.secho("\n" + "="*50, fg='cyan', bold=True)
    click.secho("REROUTE Project Initialization", fg='cyan', bold=True)
    click.secho("="*50 + "\n", fg='cyan', bold=True)

    # Interactive prompts if not provided via flags
    if not name:
        name = questionary.text(
            "Project name:",
            validate=lambda text: _validate_project_name(text),
            style=custom_style
        ).ask()
        if not name:
            click.secho("\n[ERROR] Project name is required!", fg='red', bold=True)
            sys.exit(1)
    else:
        # Validate name even if provided via flag
        validation_result = _validate_project_name(name)
        if validation_result is not True:
            click.secho(f"\n[ERROR] {validation_result}", fg='red', bold=True)
            sys.exit(1)

    project_dir = Path.cwd() / name

    if not framework:
        framework = questionary.select(
            "Which framework would you like to use?",
            choices=['fastapi', 'flask'],
            style=custom_style
        ).ask()
        if not framework:
            click.secho("\n[ERROR] Framework selection is required!", fg='red', bold=True)
            sys.exit(1)

    # Ask about test cases
    generate_tests = questionary.select(
        "Would you like to generate test cases?",
        choices=['Yes', 'No'],
        default='Yes',
        style=custom_style
    ).ask()
    include_tests = generate_tests == 'Yes'

    # Review section - show configuration
    click.secho("\n" + "="*50, fg='yellow', bold=True)
    click.secho("Project Configuration Review", fg='yellow', bold=True)
    click.secho("="*50, fg='yellow', bold=True)
    click.secho(f"  Project Name: ", fg='blue', nl=False)
    click.secho(name, fg='green', bold=True)
    click.secho(f"  Framework: ", fg='blue', nl=False)
    click.secho(framework.upper(), fg='green', bold=True)
    click.secho(f"  Host: ", fg='blue', nl=False)
    click.secho(host, fg='green')
    click.secho(f"  Port: ", fg='blue', nl=False)
    click.secho(str(port), fg='green')
    click.secho(f"  Include Tests: ", fg='blue', nl=False)
    click.secho("Yes" if include_tests else "No", fg='green')
    click.secho("="*50 + "\n", fg='yellow', bold=True)

    # Ask for confirmation
    confirm = questionary.select(
        "Does this look correct?",
        choices=['Yes, create the project', 'No, cancel'],
        default='Yes, create the project',
        style=custom_style
    ).ask()

    if confirm == 'No, cancel':
        click.secho("\n[CANCELLED] Project creation cancelled by user.\n", fg='yellow')
        sys.exit(0)

    try:
        # Create project structure
        click.secho(f"Creating project: ", fg='blue', nl=False)
        click.secho(name, fg='green', bold=True)
        _create_project_structure(project_dir, framework)

        # Generate config file
        click.secho("Creating config.py...", fg='blue')
        _generate_config_file(project_dir, config, host, port)

        # Generate logger file
        click.secho("Creating logger.py...", fg='blue')
        _generate_logger_file(project_dir, name)

        # Generate main app file
        click.secho(f"Generating {framework.upper()} application...", fg='blue')
        _generate_app_file(project_dir, name, framework, config, host, port, description)

        # Generate example route
        click.secho("Creating example route...", fg='blue')
        _generate_example_route(project_dir)

        # Generate test cases if requested
        if include_tests:
            click.secho("Creating test cases...", fg='blue')
            _generate_tests(project_dir, framework)

        # Create requirements.txt
        click.secho("Creating requirements.txt...", fg='blue')
        _create_requirements(project_dir, framework, include_tests)

        click.secho("\n" + "="*50, fg='green', bold=True)
        click.secho("[OK] Project created successfully!", fg='green', bold=True)
        click.secho("="*50 + "\n", fg='green', bold=True)

        # Show next steps
        click.secho("Next steps:", fg='yellow', bold=True)
        click.secho(f"  cd {name}", fg='cyan')
        click.secho("  pip install -r requirements.txt", fg='cyan')
        click.secho("  Happy Coding", fg='cyan')
        if framework == 'fastapi':
            click.secho(f"  python main.py", fg='cyan')
        click.secho(f"\nAPI Docs: ", fg='yellow', nl=False)
        click.secho(f"http://localhost:{port}/docs\n", fg='magenta', bold=True)


    except Exception as e:
        click.secho(f"\n[ERROR] Failed to create project: {e}", fg='red', bold=True)
        sys.exit(1)


@cli.group()
def generate():
    """
    Generate code (routes, CRUD, models, etc.)

    Available generators:
    - route: Generate a new route
    - crud: Generate a CRUD route with full operations
    """
    pass


@generate.command(name='route')
@click.option('--path', prompt='Route path (e.g., /users or /api/posts)',
              help='URL path for the route')
@click.option('--name', prompt='Route name (e.g., Users or Posts)',
              help='Name for the route class')
@click.option('--methods',
              default='GET,POST,PUT,DELETE',
              help='HTTP methods (comma-separated)')
@click.option('--http-test', is_flag=True, default=False,
              help='Generate HTTP test file')
def generate_route(path, name, methods, http_test):
    """
    Generate a new route file.

    Creates a class-based route with specified HTTP methods.

    Examples:
        reroute generate route
        reroute generate route --path /users --name Users
        reroute generate route --path /api/posts --name Posts --methods GET,POST
    """
    click.secho("\n" + "="*50, fg='cyan', bold=True)
    click.secho("Generating Route", fg='cyan', bold=True)
    click.secho("="*50 + "\n", fg='cyan', bold=True)

    try:
        # Validate we're in a REROUTE project
        if not _is_reroute_project():
            click.secho("[ERROR] Not in a REROUTE project directory!", fg='red', bold=True)
            click.secho("Run 'reroute init' first to create a project.", fg='yellow')
            sys.exit(1)

        # Create route
        route_dir = _create_route_directory(path)
        class_name = _to_class_name(name)
        resource_name = name.lower()

        # Render template
        template = jinja_env.get_template('class_route.py.j2')
        content = template.render(
            route_name=name,
            route_path=path,
            class_name=class_name,
            resource_name=resource_name
        )

        # Write route file
        route_file = route_dir / "page.py"
        route_file.write_text(content)

        click.secho(f"[OK] Route created: ", fg='green', bold=True, nl=False)
        click.secho(f"{route_file}", fg='cyan')
        click.secho(f"     Path: ", fg='blue', nl=False)
        click.secho(f"{path}", fg='magenta', bold=True)
        click.secho(f"     Class: ", fg='blue', nl=False)
        click.secho(f"{class_name}", fg='green', bold=True)
        click.secho(f"     Methods: ", fg='blue', nl=False)
        click.secho(f"{methods}", fg='yellow')

        # Generate HTTP test file if requested
        if http_test:
            http_file = _generate_http_test_file(path, name, 'route')
            click.secho(f"[OK] HTTP test created: ", fg='green', bold=True, nl=False)
            click.secho(f"{http_file}", fg='cyan')

        click.echo()

    except Exception as e:
        click.secho(f"\n[ERROR] Failed to generate route: {e}", fg='red', bold=True)
        sys.exit(1)


@generate.command(name='crud')
@click.option('--path', prompt='Route path (e.g., /users or /api/posts)',
              help='URL path for the CRUD resource')
@click.option('--name', prompt='Resource name (e.g., User or Post)',
              help='Name of the resource (singular)')
@click.option('--http-test', is_flag=True, default=False,
              help='Generate HTTP test file')
def generate_crud(path, name, http_test):
    """
    Generate a full CRUD route.

    Creates a route with complete Create, Read, Update, Delete operations.

    Examples:
        reroute generate crud
        reroute generate crud --path /users --name User
        reroute generate crud --path /api/posts --name Post
    """
    click.secho("\n" + "="*50, fg='cyan', bold=True)
    click.secho("Generating CRUD Route", fg='cyan', bold=True)
    click.secho("="*50 + "\n", fg='cyan', bold=True)

    try:
        # Validate we're in a REROUTE project
        if not _is_reroute_project():
            click.secho("[ERROR] Not in a REROUTE project directory!", fg='red', bold=True)
            click.secho("Run 'reroute init' first to create a project.", fg='yellow')
            sys.exit(1)

        # Create route
        route_dir = _create_route_directory(path)
        class_name = _to_class_name(name)
        resource_name = name.lower()

        # Render template
        template = jinja_env.get_template('crud_route.py.j2')
        content = template.render(
            route_name=name,
            route_path=path,
            class_name=class_name,
            resource_name=resource_name
        )

        # Write route file
        route_file = route_dir / "page.py"
        route_file.write_text(content)

        click.secho(f"[OK] CRUD route created: ", fg='green', bold=True, nl=False)
        click.secho(f"{route_file}", fg='cyan')
        click.secho(f"     Path: ", fg='blue', nl=False)
        click.secho(f"{path}", fg='magenta', bold=True)
        click.secho(f"     Class: ", fg='blue', nl=False)
        click.secho(f"{class_name}", fg='green', bold=True)
        click.secho(f"     Operations: ", fg='blue', nl=False)
        click.secho(f"CREATE, READ, UPDATE, DELETE", fg='yellow', bold=True)

        # Generate HTTP test file if requested
        if http_test:
            http_file = _generate_http_test_file(path, name, 'crud')
            click.secho(f"[OK] HTTP test created: ", fg='green', bold=True, nl=False)
            click.secho(f"{http_file}", fg='cyan')

        click.echo()

    except Exception as e:
        click.secho(f"\n[ERROR] Failed to generate CRUD route: {e}", fg='red', bold=True)
        sys.exit(1)


# Helper functions

def _validate_project_name(name: str):
    """
    Validate project name for filesystem compatibility.

    Args:
        name: Project name to validate

    Returns:
        True if valid, error message string if invalid
    """
    import re

    if not name or not name.strip():
        return "Project name cannot be empty"

    # Check minimum length
    if len(name) < 1:
        return "Project name must be at least 1 character"

    # Check for valid characters (alphanumeric, dash, underscore only)
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        return "Project name can only contain letters, numbers, dashes, and underscores"

    # Check it doesn't start with dash or underscore
    if name[0] in '-_':
        return "Project name cannot start with a dash or underscore"

    # Reserved names
    reserved = ['con', 'prn', 'aux', 'nul', 'com1', 'com2', 'com3', 'com4',
                'lpt1', 'lpt2', 'lpt3', 'test', 'tests']
    if name.lower() in reserved:
        return f"'{name}' is a reserved name, please choose another"

    # Check if directory already exists
    project_dir = Path.cwd() / name
    if project_dir.exists():
        return f"Directory '{name}' already exists"

    return True


def _create_project_structure(project_dir: Path, framework: str):
    """Create the basic project directory structure."""
    # Create directories
    (project_dir / "app" / "routes").mkdir(parents=True)

    # Create __init__.py files
    (project_dir / "app" / "__init__.py").write_text('"""Application package"""')
    (project_dir / "app" / "routes" / "__init__.py").write_text('"""Routes package"""')


def _generate_config_file(project_dir: Path, config: str, host: str, port: int):
    """Generate the config.py file using Jinja2 template."""
    template = jinja_env.get_template('config.py.j2')

    content = template.render(
        project_name=project_dir.name,
        host=host,
        port=port,
        reload=str(config == 'dev')
    )

    config_file = project_dir / "config.py"
    config_file.write_text(content)


def _generate_logger_file(project_dir: Path, name: str):
    """Generate the logger.py file using Jinja2 template."""
    template = jinja_env.get_template('logger.py.j2')

    content = template.render(project_name=name)

    logger_file = project_dir / "logger.py"
    logger_file.write_text(content)


def _generate_app_file(project_dir: Path, name: str, framework: str,
                       config: str, host: str, port: int, description: str):
    """Generate the main application file using Jinja2 template."""
    if framework == 'fastapi':
        template = jinja_env.get_template('fastapi_app.py.j2')
        config_class = 'DevConfig' if config == 'dev' else 'ProdConfig'

        content = template.render(
            project_name=name,
            description=description or f"{name} API",
            config_class=config_class,
            host=host,
            port=port,
            reload=str(config == 'dev')
        )

        # Use main.py to avoid naming conflict with app/ directory
        app_file = project_dir / "main.py"
        app_file.write_text(content)

    elif framework == 'flask':
        # TODO: Implement Flask template
        click.secho("[WARNING] Flask support coming soon!", fg='yellow')


def _generate_example_route(project_dir: Path):
    """Generate an example route to get started."""
    example_dir = project_dir / "app" / "routes" / "hello"
    example_dir.mkdir(parents=True, exist_ok=True)

    template = jinja_env.get_template('class_route.py.j2')
    content = template.render(
        route_name="Hello",
        route_path="/hello",
        class_name="HelloRoutes",
        resource_name="hello"
    )

    (example_dir / "page.py").write_text(content)


def _generate_tests(project_dir: Path, framework: str):
    """Generate test cases using Jinja2 template."""
    if framework == 'fastapi':
        # Create tests directory
        tests_dir = project_dir / "tests"
        tests_dir.mkdir(exist_ok=True)

        # Create __init__.py
        (tests_dir / "__init__.py").write_text('"""Tests package"""')

        # Generate test file
        template = jinja_env.get_template('test_fastapi.py.j2')
        content = template.render(project_name=project_dir.name)

        test_file = tests_dir / "test_main.py"
        test_file.write_text(content)
    elif framework == 'flask':
        # TODO: Implement Flask tests
        click.secho("[WARNING] Flask tests coming soon!", fg='yellow')


def _create_requirements(project_dir: Path, framework: str, include_tests: bool = False):
    """Create requirements.txt file."""
    requirements = ["reroute"]

    if framework == 'fastapi':
        requirements.extend(['fastapi', 'uvicorn[standard]'])
    elif framework == 'flask':
        requirements.append('flask')

    # Add test dependencies
    if include_tests:
        requirements.extend(['pytest', 'pytest-asyncio', 'httpx'])

    requirements_file = project_dir / "requirements.txt"
    requirements_file.write_text('\n'.join(requirements) + '\n')


def _is_reroute_project() -> bool:
    """Check if current directory is a REROUTE project."""
    app_dir = Path.cwd() / "app" / "routes"
    return app_dir.exists() and app_dir.is_dir()


def _create_route_directory(path: str) -> Path:
    """
    Create route directory from path.

    Examples:
        /users -> app/routes/users/
        /api/posts -> app/routes/api/posts/
    """
    # Clean path
    clean_path = path.strip('/').replace('/', os.sep)

    # Create directory
    route_dir = Path.cwd() / "app" / "routes" / clean_path
    route_dir.mkdir(parents=True, exist_ok=True)

    return route_dir


def _to_class_name(name: str) -> str:
    """
    Convert name to PascalCase class name.

    Examples:
        users -> UsersRoutes
        user -> UserRoutes
        blog_posts -> BlogPostsRoutes
    """
    # Remove special characters and split
    words = name.replace('_', ' ').replace('-', ' ').split()

    # Convert to PascalCase
    class_name = ''.join(word.capitalize() for word in words)

    # Add 'Routes' suffix if not present
    if not class_name.endswith('Routes'):
        class_name += 'Routes'

    return class_name


def _generate_http_test_file(path: str, name: str, template_type: str) -> Path:
    """
    Generate HTTP test file for a route.

    Args:
        path: Route path
        name: Route name
        template_type: 'route' or 'crud'

    Returns:
        Path to created HTTP test file
    """
    # Create tests directory if it doesn't exist
    tests_dir = Path.cwd() / "tests"
    tests_dir.mkdir(exist_ok=True)

    # Clean path for filename
    clean_path = path.strip('/').replace('/', '_')
    http_filename = f"{clean_path}.http"

    # Render template
    template = jinja_env.get_template(f'{template_type}.http.j2')
    content = template.render(
        route_name=name,
        route_path=path if path.startswith('/') else f'/{path}',
        resource_name=name.lower()
    )

    # Write HTTP test file
    http_file = tests_dir / http_filename
    http_file.write_text(content)

    return http_file


if __name__ == '__main__':
    cli()
