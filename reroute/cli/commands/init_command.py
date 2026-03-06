"""
REROUTE CLI - Init Command

Handles project initialization with interactive prompts.
Uses Cookiecutter for template-based project generation.
"""

import subprocess
import json
import click
from InquirerPy import inquirer
from pathlib import Path
import sys
import tempfile
import requests
from cookiecutter.main import cookiecutter
from .helpers import validate_project_name
from ..cli_utils import progress_step, success_message, next_steps, handle_error, CLIError


def get_template_requirements(template_url):
    """
    Fetch template requirements from cookiecutter.json.

    Args:
        template_url: Template identifier (e.g., 'gh:user/repo' or local path)

    Returns:
        dict: Template requirements metadata
    """
    try:
        cookiecutter_json = None

        # Handle GitHub templates
        if template_url.startswith('gh:'):
            # Convert gh:user/repo to raw GitHub URL
            repo_path = template_url[3:]  # Remove 'gh:' prefix
            raw_url = f"https://raw.githubusercontent.com/{repo_path}/main/cookiecutter.json"

            try:
                response = requests.get(raw_url, timeout=5)
                if response.status_code == 200:
                    cookiecutter_json = response.json()
            except requests.RequestException:
                pass

        # Handle local paths
        else:
            local_path = Path(template_url)
            if local_path.exists():
                json_file = local_path / "cookiecutter.json"
                if json_file.exists():
                    with open(json_file, 'r') as f:
                        cookiecutter_json = json.load(f)

        # Extract requirements if present
        if cookiecutter_json and '_requirements' in cookiecutter_json:
            return cookiecutter_json['_requirements']

        return {}

    except Exception:
        # If we can't fetch requirements, return empty dict (no special requirements)
        return {}


def prompt_database_selection():
    """
    Prompt user to select a database type.

    Returns:
        str: Selected database type (postgresql, mysql, sqlite, mongodb)
    """
    return inquirer.select(
        message="Which database would you like to use?",
        choices=[
            {'name': 'PostgreSQL (Recommended for production)', 'value': 'postgresql'},
            {'name': 'MySQL', 'value': 'mysql'},
            {'name': 'SQLite (Local file - good for development)', 'value': 'sqlite'},
            {'name': 'MongoDB (NoSQL)', 'value': 'mongodb'}
        ],
        default='postgresql'
    ).execute()


# Built-in template registry (will be expanded in future versions)
BUILTIN_TEMPLATES = {
    'base': 'gh:rerouteorg/reroute-base-template',
    'auth': 'gh:rerouteorg/reroute-auth-template',
}


@click.command()
@click.argument('name', required=False)
@click.option('--description', default='', help='Project description')
@click.option('--database', '-db', default=None,
              type=click.Choice(['postgresql', 'mysql', 'sqlite', 'mongodb', 'none'], case_sensitive=False),
              help='Database type (postgresql, mysql, sqlite, mongodb, or none) - only for auth template')
@click.option('--template', default=None,
              help='Template to use (base, auth, or GitHub URL like gh:user/repo)')
def init(name, description, database, template):
    """
    Initialize a new REROUTE project.

    Creates project structure with:
    - app/routes/ directory for file-based routing
    - Main application file (FastAPI)
    - Configuration files
    - Example route

    Templates are fetched from GitHub using Cookiecutter.

    Examples:
        reroute init
        reroute init myapi
        reroute init myapi --template base
        reroute init myapi --template auth
        reroute init myapi --template gh:user/custom-template
        reroute init myapi --database postgresql  # Only for auth template
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

    # Collect author info from git config (if available) for defaults
    try:
        default_author_name = subprocess.check_output(['git', 'config', 'user.name'], stderr=subprocess.DEVNULL).decode().strip()
        default_author_email = subprocess.check_output(['git', 'config', 'user.email'], stderr=subprocess.DEVNULL).decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        default_author_name = 'Your Name'
        default_author_email = 'you@example.com'

    # Ask for author information
    author_name = inquirer.text(
        message="Author name:",
        default=default_author_name
    ).execute()

    if not author_name:
        click.secho("\n[ERROR] Author name is required!", fg='red', bold=True)
        sys.exit(1)

    author_email = inquirer.text(
        message="Author email:",
        default=default_author_email
    ).execute()

    if not author_email:
        click.secho("\n[ERROR] Author email is required!", fg='red', bold=True)
        sys.exit(1)

    # Template selection
    if not template:
        template = inquirer.select(
            message="Which template would you like to use?",
            choices=[
                {'name': 'Base - Minimal FastAPI project with file-based routing', 'value': 'base'},
                {'name': 'Auth - JWT authentication with database integration', 'value': 'auth'},
                {'name': 'Custom - Use any Cookiecutter template from GitHub', 'value': 'custom'},
            ],
            default='base'
        ).execute()

        if template == 'custom':
            template = inquirer.text(
                message="Enter template URL (e.g., gh:username/cookiecutter-template):",
                default="gh:username/cookiecutter-template"
            ).execute()
            if not template:
                click.secho("\n[ERROR] Template URL is required for custom templates!", fg='red', bold=True)
                sys.exit(1)

    # Expand builtin templates to GitHub URLs
    if template in BUILTIN_TEMPLATES:
        template = BUILTIN_TEMPLATES[template]
    # else: use the provided template URL directly

    # Test files are always generated
    include_tests = True

    # Fetch template requirements
    template_requirements = get_template_requirements(template)

    # Database setup based on template requirements
    db_type = None

    # Check which template was selected (before URL expansion)
    selected_template = template
    if template in BUILTIN_TEMPLATES.values():
        # Reverse lookup to get template key
        selected_template = next(k for k, v in BUILTIN_TEMPLATES.items() if v == template)

    # Get database requirement from template
    db_requirement = template_requirements.get('database', 'optional')

    # Handle database configuration based on template requirements
    if database and database.lower() != 'none':
        # CLI flag provided - use it
        db_type = database.lower()
    elif not database:
        # No CLI flag - check template requirements
        if db_requirement == 'none':
            # Template explicitly states no database needed
            db_type = 'none'
        elif isinstance(db_requirement, dict):
            # Detailed requirement with message
            req_type = db_requirement.get('type', 'optional')
            req_message = db_requirement.get('message', '')

            if req_type == 'required':
                if req_message:
                    click.secho(f"\n[INFO] {req_message}\n", fg='cyan')
                db_type = prompt_database_selection()
            elif req_type == 'optional':
                # Optional - ask user
                include_db = inquirer.confirm(
                    message="Would you like to set up a database?",
                    default=False
                ).execute()

                if include_db:
                    db_type = prompt_database_selection()
                else:
                    db_type = 'none'
            else:
                # Unknown type - default to none
                db_type = 'none'
        elif db_requirement == 'required':
            # Simple required string
            click.secho("\n[INFO] This template requires a database.\n", fg='cyan')
            db_type = prompt_database_selection()
        elif db_requirement == 'optional':
            # Optional - ask user
            include_db = inquirer.confirm(
                message="Would you like to set up a database?",
                default=False
            ).execute()

            if include_db:
                db_type = prompt_database_selection()
            else:
                db_type = 'none'
        else:
            # Unknown requirement - default to none for safety
            db_type = 'none'
    else:
        # Database flag was explicitly set to 'none'
        db_type = 'none'

    # Review section - show configuration
    click.secho("\n" + "="*50, fg='yellow', bold=True)
    click.secho("Project Configuration Review", fg='yellow', bold=True)
    click.secho("="*50, fg='yellow', bold=True)
    click.secho(f"  Project Name: ", fg='blue', nl=False)
    click.secho(name, fg='green', bold=True)
    click.secho(f"  Author: ", fg='blue', nl=False)
    click.secho(f"{author_name} <{author_email}>", fg='green')
    click.secho(f"  Template: ", fg='blue', nl=False)
    click.secho(template, fg='green')
    if db_type and db_type != 'none':
        click.secho(f"  Database: ", fg='blue', nl=False)
        click.secho(db_type.upper(), fg='green', bold=True)
    click.secho("="*50 + "\n", fg='yellow', bold=True)

    # Validate template requirements are met
    if isinstance(db_requirement, dict) and db_requirement.get('type') == 'required':
        if not db_type or db_type == 'none':
            req_message = db_requirement.get('message', 'This template requires a database')
            click.secho(f"\n[ERROR] {req_message}", fg='red', bold=True)
            sys.exit(1)
    elif db_requirement == 'required':
        if not db_type or db_type == 'none':
            click.secho("\n[ERROR] This template requires a database!", fg='red', bold=True)
            sys.exit(1)

    # Ask for confirmation
    confirm = inquirer.confirm(
        message="Does this look correct?",
        default=True
    ).execute()

    if not confirm:
        click.secho("\n[CANCELLED] Project creation cancelled by user.\n", fg='yellow')
        sys.exit(0)

    try:
        # Prepare Cookiecutter context
        context = {
            'project_name': name,
            'description': description or f"{name} API",
            'author_name': author_name,
            'author_email': author_email,
            'include_tests': True,
            'include_database': db_type and db_type != 'none',
            'database_type': db_type or 'none',
        }

        click.secho(f"\nCreating project: ", fg='blue', nl=False)
        click.secho(name, fg='green', bold=True)
        click.echo()

        with progress_step("Fetching template and generating project"):
            # Generate project using Cookiecutter
            result = cookiecutter(
                template=template,
                no_input=True,
                extra_context=context,
                output_dir='.'
            )

        # Verify project was created
        generated_dir = Path(result)
        if not generated_dir.exists():
            raise CLIError(
                "Project directory was not created",
                suggestion="Check that the template URL is correct and accessible",
                error_code="E001"
            )

        # Success message
        success_message("Project created successfully!", {
            "Project": name,
            "Template": template,
            "Location": str(generated_dir)
        })

        # Show database-specific tips if database was configured
        if db_type and db_type != 'none':
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

        # Show next steps using utility (uv only as of v0.3.0)
        steps = [
            f"cd {name}",
            "uv venv",
            "uv sync",
            "uv run main.py",
        ]
        next_steps(steps)

        click.secho("Happy Coding!", fg='yellow', bold=True)
        click.secho(f"\nAPI Docs: ", fg='yellow', nl=False)
        click.secho(f"http://localhost:7376/docs\n", fg='magenta', bold=True)

    except CLIError as e:
        handle_error(e, context="Project creation")
        sys.exit(1)
    except Exception as e:
        handle_error(e, context="Failed to create project")
        sys.exit(1)