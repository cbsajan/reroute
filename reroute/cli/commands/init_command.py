"""
REROUTE CLI - Init Command

Handles project initialization with interactive prompts.
"""

import click
from InquirerPy import inquirer
from pathlib import Path
import sys
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .helpers import validate_project_name
from ..utils import progress_step, success_message, next_steps, handle_error, CLIError

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
              help='Backend framework (fastapi or flask)')
@click.option('--package-manager', default='uv',
              type=click.Choice(['uv', 'pip']),
              help='Package manager (default: uv)')
@click.option('--config',
              type=click.Choice(['dev', 'prod'], case_sensitive=False),
              default='dev',
              help='Configuration type (dev or prod)')
@click.option('--host', default='0.0.0.0', help='Server host')
@click.option('--port', default=7376, type=int, help='Server port')
@click.option('--description', default='', help='Project description')
@click.option('--database', '-db', default=None,
              type=click.Choice(['postgresql', 'mysql', 'sqlite', 'mongodb', 'none'], case_sensitive=False),
              help='Database type (postgresql, mysql, sqlite, mongodb, or none)')
def init(name, framework, package_manager, config, host, port, description, database):
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
        reroute init myapi --framework fastapi --database postgresql
        reroute init myapi -db sqlite
    """
    click.secho("\n" + "="*50, fg='cyan', bold=True)
    click.secho("REROUTE Project Initialization", fg='cyan', bold=True)
    click.secho("="*50 + "\n", fg='cyan', bold=True)

    # Interactive prompts if not provided via flags
    if not name:
        name = inquirer.text(
            message="Project name:",
            validate=lambda text: validate_project_name(text) is True,
            invalid_message=lambda text: validate_project_name(text) if validate_project_name(text) is not True else ""
        ).execute()
        if not name:
            click.secho("\n[ERROR] Project name is required!", fg='red', bold=True)
            sys.exit(1)
    else:
        # Validate name even if provided via flag
        validation_result = validate_project_name(name)
        if validation_result is not True:
            click.secho(f"\n[ERROR] {validation_result}", fg='red', bold=True)
            sys.exit(1)

    # Convert project name to lowercase for consistency
    name = name.lower()

    project_dir = Path.cwd() / name

    if not framework:
        framework = inquirer.select(
            message="Which framework would you like to use?",
            choices=['fastapi', 'flask']
        ).execute()
        if not framework:
            click.secho("\n[ERROR] Framework selection is required!", fg='red', bold=True)
            sys.exit(1)
    else:
        # Validate and normalize CLI flag input (case-insensitive)
        framework_lower = framework.lower()
        if framework_lower not in ['fastapi', 'flask']:
            click.secho(f"\n[ERROR] Invalid framework: '{framework}'. Choose 'fastapi' or 'flask'.", fg='red', bold=True)
            sys.exit(1)
        framework = framework_lower

    # Ask about test cases
    generate_tests = inquirer.select(
        message="Would you like to generate test cases?",
        choices=['Yes', 'No'],
        default='Yes'
    ).execute()
    include_tests = generate_tests == 'Yes'

    # Database setup (available in v0.2.0+)
    db_type = None
    if database and database.lower() != 'none':
        # CLI flag provided
        db_type = database.lower()
    elif not database:
        # No flag provided - prompt user
        include_db = inquirer.confirm(
            message="Would you like to set up a database?",
            default=False
        ).execute()

        if include_db:
            db_type = inquirer.select(
                message="Which database would you like to use?",
                choices=[
                    {'name': 'PostgreSQL', 'value': 'postgresql'},
                    {'name': 'MySQL', 'value': 'mysql'},
                    {'name': 'SQLite (Local file)', 'value': 'sqlite'},
                    {'name': 'MongoDB (NoSQL)', 'value': 'mongodb'}
                ],
                default='postgresql'
            ).execute()

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
    if db_type:
        click.secho(f"  Database: ", fg='blue', nl=False)
        click.secho(db_type.upper(), fg='green', bold=True)
    click.secho("="*50 + "\n", fg='yellow', bold=True)

    # Ask for confirmation
    confirm = inquirer.confirm(
        message="Does this look correct?",
        default=True
    ).execute()

    if not confirm:
        click.secho("\n[CANCELLED] Project creation cancelled by user.\n", fg='yellow')
        sys.exit(0)

    try:
        # Create project structure with progress indicators
        click.secho(f"\nCreating project: ", fg='blue', nl=False)
        click.secho(name, fg='green', bold=True)
        click.echo()

        with progress_step("Creating project structure"):
            _create_project_structure(project_dir, framework)

        with progress_step("Creating config.py"):
            _generate_config_file(project_dir, config, host, port)

        with progress_step("Creating logger.py"):
            _generate_logger_file(project_dir, name)

        with progress_step(f"Generating {framework.upper()} application"):
            _generate_app_file(project_dir, name, framework, config, host, port, description)

        with progress_step("Creating example route"):
            _generate_example_route(project_dir)

        with progress_step("Creating root and health routes"):
            _generate_root_route(project_dir, framework, name)

        if include_tests:
            with progress_step("Creating test cases"):
                _generate_tests(project_dir, framework)

        with progress_step("Creating .env.example"):
            _generate_env_file(project_dir, name, db_type, package_manager)

        if db_type:
            with progress_step("Creating database configuration"):
                _generate_database_files(project_dir, name, db_type)

        with progress_step("Creating requirements.txt"):
            _create_requirements(project_dir, framework, include_tests, db_type)

        with progress_step("Creating pyproject.toml"):
            _create_pyproject(project_dir, name, framework, include_tests, db_type, package_manager)

        # Success message
        success_message("Project created successfully!", {
            "Project": name,
            "Framework": framework.upper(),
            "Location": str(project_dir)
        })

        # Show database-specific tips if database was configured
        if db_type:
            click.secho(f"  {click.style('[OK]', fg='green')} Database configuration created (app/database.py)")
            click.secho(f"  {click.style('[OK]', fg='green')} Sample User model created (app/db_models/user.py)")
            click.secho("")
            click.secho(f"  {click.style('[TIP]', fg='cyan')} Next steps for database:")
            click.secho(f"    {click.style('1.', fg='yellow')} Copy .env.example to .env and update DATABASE_URL")
            click.secho(f"    {click.style('2.', fg='yellow')} Run: {click.style('reroute db init', fg='bright_white')}")
            migrate_cmd = "reroute db migrate -m 'initial'"
            click.secho(f"    {click.style('3.', fg='yellow')} Run: {click.style(migrate_cmd, fg='bright_white')}")
            click.secho(f"    {click.style('4.', fg='yellow')} Run: {click.style('reroute db upgrade', fg='bright_white')}")
            click.secho("")

        # Show next steps using utility
        if package_manager == 'uv':
            steps = [
                f"cd {name}",
                "uv venv",
                "uv sync",
                "uv run main.py",
            ]
        else:
            steps = [
                f"cd {name}",
                "python -m venv venv",
                "pip install -r requirements.txt",
                "python main.py",
            ]
        next_steps(steps)

        click.secho("Happy Coding!", fg='yellow', bold=True)
        click.secho(f"\nAPI Docs: ", fg='yellow', nl=False)
        click.secho(f"http://localhost:{port}/docs\n", fg='magenta', bold=True)

    except CLIError as e:
        handle_error(e, context="Project creation")
        sys.exit(1)
    except Exception as e:
        handle_error(e, context="Failed to create project")
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

        content = template.render(
            project_name=name,
            description=description or f"{name} API"
        )

        # Use main.py to avoid naming conflict with app/ directory
        app_file = project_dir / "main.py"
        app_file.write_text(content)

    elif framework == 'flask':
        template = jinja_env.get_template('app/flask_app.py.j2')

        content = template.render(
            project_name=name
        )

        # Use main.py to avoid naming conflict with app/ directory
        app_file = project_dir / "main.py"
        app_file.write_text(content)


def _generate_example_route(project_dir: Path):
    """Generate an example route to get started."""
    example_dir = project_dir / "app" / "routes" / "hello"
    example_dir.mkdir(parents=True, exist_ok=True)

    template = jinja_env.get_template('routes/class_route.py.j2')
    content = template.render(
        route_name="Hello",
        route_path="/hello",
        methods=["GET", "POST", "PUT", "DELETE"],
        class_name="HelloRoutes",
        resource_name="hello"
    )

    (example_dir / "page.py").write_text(content)


def _generate_root_route(project_dir: Path, framework: str, name: str):
    """Generate the root and health routes in app folder (combined in one file)."""
    # Generate combined root and health routes
    template = jinja_env.get_template('app/root.py.j2')
    content = template.render(
        framework=framework,
        project_name=name
    )

    # Create the route file in app/
    app_dir = project_dir / "app"
    app_dir.mkdir(parents=True, exist_ok=True)

    route_file = app_dir / "root.py"
    route_file.write_text(content)


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
        # Create tests directory
        tests_dir = project_dir / "tests"
        tests_dir.mkdir(exist_ok=True)

        # Create __init__.py
        (tests_dir / "__init__.py").write_text('"""Tests package"""')

        # Generate test file
        template = jinja_env.get_template('tests/test_flask.py.j2')
        content = template.render(project_name=project_dir.name)

        test_file = tests_dir / "test_main.py"
        test_file.write_text(content)


def _create_requirements(project_dir: Path, framework: str, include_tests: bool = False, db_type: str = None):
    """Create requirements.txt using template."""
    template = jinja_env.get_template('project/requirements.txt.j2')
    content = template.render(
        framework=framework,
        db_type=db_type,
        include_tests=include_tests
    )
    requirements_file = project_dir / "requirements.txt"
    requirements_file.write_text(content)


def _create_pyproject(project_dir: Path, project_name: str, framework: str, include_tests: bool = False, db_type: str = None, package_manager: str = 'uv'):
    """Create pyproject.toml using template (modern Python standard, uv-compatible)."""
    template = jinja_env.get_template('project/pyproject.toml.j2')
    content = template.render(
        project_name=project_name,
        framework=framework,
        db_type=db_type,
        include_tests=include_tests,
        package_manager=package_manager
    )
    pyproject_file = project_dir / "pyproject.toml"
    pyproject_file.write_text(content)


def _generate_env_file(project_dir: Path, name: str, db_type: str = None, package_manager: str = 'uv'):
    """Generate .env.example file."""
    template = jinja_env.get_template('project/env.example.j2')

    # Set default URL based on db_type (with obvious placeholders)
    db_url = None
    valid_db_types = {'postgresql', 'mysql', 'sqlite', 'mongodb'}
    if db_type and db_type in valid_db_types:
        default_urls = {
            'postgresql': f'postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/{name}',
            'mysql': f'mysql+pymysql://YOUR_USER:YOUR_PASSWORD@localhost:3306/{name}',
            'sqlite': f'sqlite:///./{name}.db',
            'mongodb': f'mongodb://localhost:27017/{name}'
        }
        db_url = default_urls.get(db_type, '')

    # Determine install command based on package manager
    install_cmd = 'uv sync' if package_manager == 'uv' else 'pip install -e .'

    content = template.render(
        project_name=name,
        db_type=db_type,
        db_url=db_url,
        package_manager=package_manager,
        install_cmd=install_cmd
    )
    env_file = project_dir / ".env.example"
    env_file.write_text(content)


def _generate_database_files(project_dir: Path, name: str, db_type: str):
    """Generate database configuration and sample model."""

    # Validate db_type to prevent unexpected values
    valid_db_types = {'postgresql', 'mysql', 'sqlite', 'mongodb'}
    if db_type not in valid_db_types:
        raise ValueError(f"Invalid db_type: {db_type}. Must be one of {valid_db_types}")

    # Set default URL based on db_type (with obvious placeholders - NEVER use in production)
    default_urls = {
        'postgresql': f'postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/{name}',
        'mysql': f'mysql+pymysql://YOUR_USER:YOUR_PASSWORD@localhost:3306/{name}',
        'sqlite': f'sqlite:///./{name}.db',
        'mongodb': f'mongodb://localhost:27017/{name}'
    }

    # Create app/database.py
    db_template = jinja_env.get_template('database/database.py.j2')
    db_content = db_template.render(
        name=name,
        db_type=db_type,
        default_url=default_urls.get(db_type, '')
    )
    (project_dir / "app" / "database.py").write_text(db_content)

    # Create app/db_models/ directory
    db_models_dir = project_dir / "app" / "db_models"
    db_models_dir.mkdir(exist_ok=True)
    (db_models_dir / "__init__.py").write_text('"""Database models"""')

    # Create sample User model
    user_template = jinja_env.get_template('database/user_model.py.j2')
    user_content = user_template.render(db_type=db_type)
    (db_models_dir / "user.py").write_text(user_content)
