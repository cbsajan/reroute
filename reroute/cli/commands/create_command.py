"""
REROUTE CLI - Create/Generate Commands

Handles code generation for routes, CRUD, and models.
"""

import click
from pathlib import Path
import sys
import re
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .helpers import is_reroute_project, create_route_directory, to_class_name, auto_name_from_path, check_class_name_duplicate, validate_route_path, validate_path_realtime

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
@click.option('--path', default=None,
              callback=validate_route_path,
              help='URL path for the route')
@click.option('--name', default=None,
              help='Name for the route class (auto-generated from path if not provided)')
@click.option('--methods',
              default=None,
              help='HTTP methods (comma-separated). If not provided, interactive selection will be shown.')
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

        # Prompt for path if not provided (with real-time validation)
        if path is None:
            path = inquirer.text(
                message="Route path (e.g., /users or /api/posts):",
                validate=validate_path_realtime,
                invalid_message="Path must start with / and not end with / (e.g., /user, /api/posts)"
            ).execute()

        # Auto-generate name from path if not provided
        if name is None:
            auto_generated_name = auto_name_from_path(path)

            # Ask for confirmation
            use_auto_name = inquirer.confirm(
                message=f'Use generated name "{auto_generated_name}"?',
                default=True
            ).execute()

            if use_auto_name:
                name = auto_generated_name
                click.secho(f"\nFinal Route Name: {name}", fg='green', bold=True)
            else:
                # Ask for custom name with validation
                def validate_custom_name(text):
                    import re
                    if not text or not text.strip():
                        return False
                    text = text.strip()
                    # Must contain only alphanumeric, dashes, underscores
                    # and must start with a letter (after stripping underscores)
                    text_no_underscore = text.lstrip('_')
                    if not text_no_underscore:
                        return False
                    if not text_no_underscore[0].isalpha():
                        return False
                    if not re.match(r'^[a-zA-Z0-9_-]+$', text):
                        return False
                    return True

                name = inquirer.text(
                    message="Enter your custom route name:",
                    validate=validate_custom_name,
                    invalid_message="Invalid name. Must start with a letter and contain only letters, numbers, dashes, underscores."
                ).execute()
                click.secho(f"\nFinal Route Name: {name}", fg='green', bold=True)

        # Prepare class name and resource name
        class_name = to_class_name(name)
        resource_name = name.lower()

        # Calculate route directory path (without creating it yet)
        routes_dir = Path.cwd() / "app" / "routes"
        route_path_clean = path.strip('/').replace('/', Path('/').as_posix())
        route_dir = routes_dir / route_path_clean
        route_file = route_dir / "page.py"

        # Check for duplicate class name
        if check_class_name_duplicate(class_name, route_dir):
            click.secho(f"\n[ERROR] Class '{class_name}' already exists in {route_file}!", fg='red', bold=True)
            click.secho(f"Choose a different name or delete the existing route first.", fg='yellow')
            sys.exit(1)

        # Parse methods - use interactive checkbox if not provided
        if methods is None:
            # Interactive method selection
            selected_methods = inquirer.checkbox(
                message="Select HTTP methods to generate:",
                choices=[
                    Choice("GET", enabled=True),
                    Choice("POST", enabled=True),
                    Choice("PUT", enabled=False),
                    Choice("PATCH", enabled=False),
                    Choice("DELETE", enabled=False),
                ],
                validate=lambda result: len(result) >= 1,
                invalid_message="At least one method must be selected"
            ).execute()

            methods_list = selected_methods
        else:
            # Parse comma-separated methods
            methods_list = [m.strip().upper() for m in methods.split(',')]

        # Check if route already exists
        existing_methods = _extract_existing_methods(route_file)
        is_updating = len(existing_methods) > 0

        if is_updating:
            # Merge new methods with existing ones
            combined_methods = list(set(existing_methods + methods_list))
            combined_methods.sort(key=lambda x: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'].index(x) if x in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'] else 999)

            new_methods = [m for m in methods_list if m not in existing_methods]

            if not new_methods:
                click.secho(f"[INFO] Methods {', '.join(methods_list)} already exist in route!", fg='yellow', bold=True)
                click.secho(f"       Existing methods: {', '.join(existing_methods)}", fg='cyan')
                return

            methods_list = combined_methods
            click.secho(f"\n[INFO] Route already exists. Adding new methods...", fg='cyan', bold=True)
            click.secho(f"       Existing: {', '.join(existing_methods)}", fg='magenta')
            click.secho(f"       Adding: {', '.join(new_methods)}", fg='green')
            click.secho(f"       Final: {', '.join(methods_list)}", fg='yellow', bold=True)
            click.echo()

        # Render template
        template = jinja_env.get_template('routes/class_route.py.j2')
        content = template.render(
            route_name=name,
            route_path=path,
            class_name=class_name,
            resource_name=resource_name,
            methods=methods_list
        )

        # NOW create the directory (after all validations and inputs are complete)
        route_dir.mkdir(parents=True, exist_ok=True)

        # Write route file
        route_file.write_text(content)

        if is_updating:
            click.secho(f"[OK] Route updated: ", fg='green', bold=True, nl=False)
        else:
            click.secho(f"[OK] Route created: ", fg='green', bold=True, nl=False)

        click.secho(f"{route_file}", fg='cyan')
        click.secho(f"     Path: ", fg='blue', nl=False)
        click.secho(f"{path}", fg='magenta', bold=True)
        click.secho(f"     Class: ", fg='blue', nl=False)
        click.secho(f"{class_name}", fg='green', bold=True)
        click.secho(f"     Methods: ", fg='blue', nl=False)
        click.secho(f"{', '.join(methods_list)}", fg='yellow')

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
@click.option('--path', default=None,
              callback=validate_route_path,
              help='URL path for the CRUD resource')
@click.option('--name', default=None,
              help='Name of the resource (auto-generated from path if not provided)')
@click.option('--operations',
              default=None,
              help='CRUD operations (comma-separated: CREATE,READ,UPDATE,DELETE). If not provided, interactive selection will be shown.')
@click.option('--http-test', is_flag=True, default=False,
              help='Generate HTTP test file')
def generate_crud(path, name, operations, http_test):
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

        # Prompt for path if not provided (with real-time validation)
        if path is None:
            path = inquirer.text(
                message="Route path (e.g., /users or /api/posts):",
                validate=validate_path_realtime,
                invalid_message="Path must start with / and not end with / (e.g., /user, /api/posts)"
            ).execute()

        # Auto-generate name from path if not provided
        if name is None:
            auto_generated_name = auto_name_from_path(path)

            # Ask for confirmation
            use_auto_name = inquirer.confirm(
                message=f'Use generated name "{auto_generated_name}"?',
                default=True
            ).execute()

            if use_auto_name:
                name = auto_generated_name
                click.secho(f"\nFinal Resource Name: {name}", fg='green', bold=True)
            else:
                # Ask for custom name with validation
                def validate_custom_name(text):
                    import re
                    if not text or not text.strip():
                        return False
                    text = text.strip()
                    # Must contain only alphanumeric, dashes, underscores
                    # and must start with a letter (after stripping underscores)
                    text_no_underscore = text.lstrip('_')
                    if not text_no_underscore:
                        return False
                    if not text_no_underscore[0].isalpha():
                        return False
                    if not re.match(r'^[a-zA-Z0-9_-]+$', text):
                        return False
                    return True

                name = inquirer.text(
                    message="Enter your custom resource name:",
                    validate=validate_custom_name,
                    invalid_message="Invalid name. Must start with a letter and contain only letters, numbers, dashes, underscores."
                ).execute()
                click.secho(f"\nFinal Resource Name: {name}", fg='green', bold=True)

        # Prepare class name and resource name
        class_name = to_class_name(name)
        resource_name = name.lower()

        # Calculate route directory path (without creating it yet)
        routes_dir = Path.cwd() / "app" / "routes"
        route_path_clean = path.strip('/').replace('/', Path('/').as_posix())
        route_dir = routes_dir / route_path_clean
        route_file = route_dir / "page.py"

        # Check for duplicate class name
        if check_class_name_duplicate(class_name, route_dir):
            click.secho(f"\n[ERROR] Class '{class_name}' already exists in {route_file}!", fg='red', bold=True)
            click.secho(f"Choose a different name or delete the existing route first.", fg='yellow')
            sys.exit(1)

        # Parse operations - use interactive checkbox if not provided
        if operations is None:
            # Interactive operation selection
            selected_operations = inquirer.checkbox(
                message="Select CRUD operations to generate:",
                choices=[
                    Choice("CREATE (POST)", enabled=True),
                    Choice("READ (GET)", enabled=True),
                    Choice("UPDATE (PUT)", enabled=True),
                    Choice("DELETE (DELETE)", enabled=True),
                ],
                validate=lambda result: len(result) >= 1,
                invalid_message="At least one operation must be selected"
            ).execute()

            # Extract operation names (remove HTTP method hints)
            operations_list = [op.split(' ')[0] for op in selected_operations]
        else:
            # Parse comma-separated operations
            operations_list = [op.strip().upper() for op in operations.split(',')]

        # Render template
        template = jinja_env.get_template('routes/crud_route.py.j2')
        content = template.render(
            route_name=name,
            route_path=path,
            class_name=class_name,
            resource_name=resource_name,
            operations=operations_list
        )

        # NOW create the directory (after all validations and inputs are complete)
        route_dir.mkdir(parents=True, exist_ok=True)

        # Write route file
        route_file.write_text(content)

        click.secho(f"[OK] CRUD route created: ", fg='green', bold=True, nl=False)
        click.secho(f"{route_file}", fg='cyan')
        click.secho(f"     Path: ", fg='blue', nl=False)
        click.secho(f"{path}", fg='magenta', bold=True)
        click.secho(f"     Class: ", fg='blue', nl=False)
        click.secho(f"{class_name}", fg='green', bold=True)
        click.secho(f"     Operations: ", fg='blue', nl=False)
        click.secho(f"{', '.join(operations_list)}", fg='yellow', bold=True)

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
@click.option('--name', default=None,
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

        # Prompt for name if not provided (with real-time validation)
        if name is None:
            def validate_model_name(text):
                """Real-time validation for model name"""
                import re
                if not text or not text.strip():
                    return False
                text = text.strip()
                # Must contain only alphanumeric, dashes, underscores
                text_no_underscore = text.lstrip('_')
                if not text_no_underscore:
                    return False
                if not text_no_underscore[0].isalpha():
                    return False
                if not re.match(r'^[a-zA-Z0-9_-]+$', text):
                    return False
                return True

            name = inquirer.text(
                message="Model name (e.g., User or Post):",
                validate=validate_model_name,
                invalid_message="Model name must start with a letter and contain only letters, numbers, dashes, underscores."
            ).execute()

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
@click.option('--path', default=None,
              callback=validate_route_path,
              help='URL path for the route')
@click.option('--name', default=None,
              help='Name for the route class (auto-generated from path if not provided)')
@click.option('--methods',
              default=None,
              help='HTTP methods (comma-separated). If not provided, interactive selection will be shown.')
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
@click.option('--path', default=None,
              callback=validate_route_path,
              help='URL path for the CRUD resource')
@click.option('--name', default=None,
              help='Name of the resource (auto-generated from path if not provided)')
@click.option('--operations',
              default=None,
              help='CRUD operations (comma-separated: CREATE,READ,UPDATE,DELETE). If not provided, interactive selection will be shown.')
@click.option('--http-test', is_flag=True, default=False,
              help='Generate HTTP test file')
def create_crud(path, name, operations, http_test):
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
    ctx.invoke(generate_crud, path=path, name=name, operations=operations, http_test=http_test)


@create.command(name='model')
@click.option('--name', default=None,
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

def _extract_existing_methods(route_file: Path) -> list:
    """
    Extract existing HTTP methods from a route file.

    Args:
        route_file: Path to the existing route file

    Returns:
        List of existing HTTP methods (uppercase)
    """
    if not route_file.exists():
        return []

    content = route_file.read_text()
    existing_methods = []

    # Look for method definitions: def get(self):, def post(self):, etc.
    method_pattern = r'def\s+(get|post|put|patch|delete)\s*\('
    matches = re.finditer(method_pattern, content, re.IGNORECASE)

    for match in matches:
        method = match.group(1).upper()
        if method not in existing_methods:
            existing_methods.append(method)

    return existing_methods


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
