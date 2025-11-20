"""
REROUTE CLI - Init Command

Handles project initialization with interactive prompts.
"""

import click
import questionary
from questionary import Style
from pathlib import Path
import sys
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .helpers import validate_project_name

# Custom style for questionary prompts
custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#2196f3 bold'),
    ('pointer', 'fg:#673ab7 bold'),
    ('highlighted', 'fg:#2196f3 bold'),
    ('selected', 'fg:#4caf50 bold'),
    ('separator', 'fg:#cc5454'),
    ('instruction', ''),
    ('text', ''),
    ('disabled', 'fg:#858585 italic')
])

# Setup Jinja2 environment
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True
)


@click.command()
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
        reroute init myapi --framework fastapi
    """
    click.secho("\n" + "="*50, fg='cyan', bold=True)
    click.secho("REROUTE Project Initialization", fg='cyan', bold=True)
    click.secho("="*50 + "\n", fg='cyan', bold=True)

    # Interactive prompts if not provided via flags
    if not name:
        name = questionary.text(
            "Project name:",
            validate=lambda text: validate_project_name(text),
            style=custom_style
        ).ask()
        if not name:
            click.secho("\n[ERROR] Project name is required!", fg='red', bold=True)
            sys.exit(1)
    else:
        # Validate name even if provided via flag
        validation_result = validate_project_name(name)
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
        if framework == 'fastapi':
            click.secho(f"  python main.py", fg='cyan')
        click.secho("\nHappy Coding!", fg='yellow', bold=True)
        click.secho(f"\nAPI Docs: ", fg='yellow', nl=False)
        click.secho(f"http://localhost:{port}/docs\n", fg='magenta', bold=True)

    except Exception as e:
        click.secho(f"\n[ERROR] Failed to create project: {e}", fg='red', bold=True)
        sys.exit(1)


# Helper functions

def _create_project_structure(project_dir: Path, framework: str):
    """Create the basic project directory structure."""
    # Create directories
    (project_dir / "app" / "routes").mkdir(parents=True)

    # Create __init__.py files
    (project_dir / "app" / "__init__.py").write_text('"""Application package"""')
    (project_dir / "app" / "routes" / "__init__.py").write_text('"""Routes package"""')


def _generate_config_file(project_dir: Path, config: str, host: str, port: int):
    """Generate the config.py file using Jinja2 template."""
    template = jinja_env.get_template('config/config.py.j2')

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
    template = jinja_env.get_template('config/logger.py.j2')

    content = template.render(project_name=name)

    logger_file = project_dir / "logger.py"
    logger_file.write_text(content)


def _generate_app_file(project_dir: Path, name: str, framework: str,
                       config: str, host: str, port: int, description: str):
    """Generate the main application file using Jinja2 template."""
    if framework == 'fastapi':
        template = jinja_env.get_template('app/fastapi_app.py.j2')
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

    template = jinja_env.get_template('routes/class_route.py.j2')
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
        template = jinja_env.get_template('tests/test_fastapi.py.j2')
        content = template.render(project_name=project_dir.name)

        test_file = tests_dir / "test_main.py"
        test_file.write_text(content)
    elif framework == 'flask':
        # TODO: Implement Flask tests
        click.secho("[WARNING] Flask tests coming soon!", fg='yellow')


def _create_requirements(project_dir: Path, framework: str, include_tests: bool = False):
    """Create requirements.txt using template."""
    template = jinja_env.get_template('project/requirements.txt.j2')
    content = template.render(
        framework=framework,
        db_type=None,
        include_tests=include_tests
    )
    requirements_file = project_dir / "requirements.txt"
    requirements_file.write_text(content)
