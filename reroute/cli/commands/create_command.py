"""
REROUTE CLI - Create/Generate Commands

Handles code generation for routes, CRUD, and models.
"""

import click
from pathlib import Path
import sys
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .helpers import is_reroute_project, create_route_directory, to_class_name

# Setup Jinja2 environment
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True
)


@click.group()
def generate():
    """
    Generate code (routes, CRUD, models, etc.)

    Available generators:
    - route: Generate a new route
    - crud: Generate a CRUD route with full operations
    - model: Generate a Pydantic model for data validation
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
        if not is_reroute_project():
            click.secho("[ERROR] Not in a REROUTE project directory!", fg='red', bold=True)
            click.secho("Run 'reroute init' first to create a project.", fg='yellow')
            sys.exit(1)

        # Create route
        route_dir = create_route_directory(path)
        class_name = to_class_name(name)
        resource_name = name.lower()

        # Render template
        template = jinja_env.get_template('routes/class_route.py.j2')
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
        if not is_reroute_project():
            click.secho("[ERROR] Not in a REROUTE project directory!", fg='red', bold=True)
            click.secho("Run 'reroute init' first to create a project.", fg='yellow')
            sys.exit(1)

        # Create route
        route_dir = create_route_directory(path)
        class_name = to_class_name(name)
        resource_name = name.lower()

        # Render template
        template = jinja_env.get_template('routes/crud_route.py.j2')
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


@generate.command(name='model')
@click.option('--name', prompt='Model name (e.g., User or Post)',
              help='Name of the model (singular)')
def generate_model(name):
    """
    Generate a Pydantic model for data validation.

    Creates models for CRUD operations with default fields:
    - ModelBase: Base schema with common fields
    - ModelCreate: For POST requests
    - ModelUpdate: For PUT/PATCH requests (all fields optional)
    - ModelInDB: Database representation with id, timestamps
    - ModelResponse: API response schema

    The generated model includes example fields that you can customize.

    Examples:
        reroute generate model
        reroute generate model --name User
        reroute generate model --name Post
    """
    click.secho("\n" + "="*50, fg='cyan', bold=True)
    click.secho("Generating Pydantic Model", fg='cyan', bold=True)
    click.secho("="*50 + "\n", fg='cyan', bold=True)

    try:
        # Validate we're in a REROUTE project
        if not is_reroute_project():
            click.secho("[ERROR] Not in a REROUTE project directory!", fg='red', bold=True)
            click.secho("Run 'reroute init' first to create a project.", fg='yellow')
            sys.exit(1)

        # Create models directory if it doesn't exist
        models_dir = Path.cwd() / "app" / "models"
        models_dir.mkdir(parents=True, exist_ok=True)

        # Create __init__.py in models directory if it doesn't exist
        init_file = models_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""Models package"""\n')

        # Generate model file
        class_name = to_class_name(name)
        model_filename = name.lower() + ".py"
        model_file = models_dir / model_filename

        # Render template with default content
        template = jinja_env.get_template('models/model.py.j2')
        content = template.render(
            model_name=class_name
        )

        # Write model file
        model_file.write_text(content)

        click.secho(f"[OK] Model created: ", fg='green', bold=True, nl=False)
        click.secho(f"{model_file}", fg='cyan')
        click.secho(f"     Model: ", fg='blue', nl=False)
        click.secho(f"{class_name}", fg='green', bold=True)
        click.secho(f"     Schemas: ", fg='blue', nl=False)
        click.secho(f"{class_name}Base, {class_name}Create, {class_name}Update, {class_name}InDB, {class_name}Response", fg='yellow')

        click.secho(f"\n[NOTE] Generated with default fields: ", fg='blue', nl=False)
        click.secho("name, description, is_active", fg='magenta')
        click.secho("[TIP] Customize the fields in the generated file to match your requirements.", fg='yellow')

        click.secho(f"\n[TIP] Import with: ", fg='blue', nl=False)
        click.secho(f"from app.models.{name.lower()} import {class_name}Create, {class_name}Response", fg='cyan')

        click.echo()

    except Exception as e:
        click.secho(f"\n[ERROR] Failed to generate model: {e}", fg='red', bold=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


# Create command group (alias for generate, more intuitive)
@click.group()
def create():
    """
    Create routes and components (alias for 'generate').

    Available options:
    - route: Create a new route
    - crud: Create a CRUD route with full operations
    - model: Create a Pydantic model for data validation
    """
    pass


# Add route subcommand to create (mirrors generate route)
@create.command(name='route')
@click.option('--path', prompt='Route path (e.g., /users or /api/posts)',
              help='URL path for the route')
@click.option('--name', prompt='Route name (e.g., Users or Posts)',
              help='Name for the route class')
@click.option('--methods',
              default='GET,POST,PUT,DELETE',
              help='HTTP methods (comma-separated)')
@click.option('--http-test', is_flag=True, default=False,
              help='Generate HTTP test file')
def create_route(path, name, methods, http_test):
    """
    Create a new route file.

    This is an alias for 'reroute generate route'.
    Creates a class-based route with specified HTTP methods.

    Examples:
        reroute create route
        reroute create route --path /users --name Users
    """
    # Call the same logic as generate_route
    from click import Context
    ctx = Context(generate_route)
    ctx.invoke(generate_route, path=path, name=name, methods=methods, http_test=http_test)


@create.command(name='crud')
@click.option('--path', prompt='Route path (e.g., /users or /api/posts)',
              help='URL path for the CRUD resource')
@click.option('--name', prompt='Resource name (e.g., User or Post)',
              help='Name of the resource (singular)')
@click.option('--http-test', is_flag=True, default=False,
              help='Generate HTTP test file')
def create_crud(path, name, http_test):
    """
    Create a full CRUD route.

    This is an alias for 'reroute generate crud'.
    Creates a route with complete Create, Read, Update, Delete operations.

    Examples:
        reroute create crud
        reroute create crud --path /users --name User
    """
    # Call the same logic as generate_crud
    from click import Context
    ctx = Context(generate_crud)
    ctx.invoke(generate_crud, path=path, name=name, http_test=http_test)


@create.command(name='model')
@click.option('--name', prompt='Model name (e.g., User or Post)',
              help='Name of the model (singular)')
def create_model(name):
    """
    Create a Pydantic model.

    This is an alias for 'reroute generate model'.
    Creates models for data validation and CRUD operations with default fields.

    Examples:
        reroute create model
        reroute create model --name User
    """
    # Call the same logic as generate_model
    from click import Context
    ctx = Context(generate_model)
    ctx.invoke(generate_model, name=name)


# Helper functions

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
    template = jinja_env.get_template(f'http/{template_type}.http.j2')
    content = template.render(
        route_name=name,
        route_path=path if path.startswith('/') else f'/{path}',
        resource_name=name.lower()
    )

    # Write HTTP test file
    http_file = tests_dir / http_filename
    http_file.write_text(content)

    return http_file
