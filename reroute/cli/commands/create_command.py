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
from .helpers import is_reroute_project, create_route_directory, to_class_name, to_pascal_case, auto_name_from_path, check_class_name_duplicate, validate_route_path, validate_path_realtime

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


@create.command(name='dbmodel', hidden=True)
@click.option('--name', default=None,
              help='Name of the database model (singular, e.g., User)')
def create_dbmodel(name):
    """
    [PREVIEW] Create a SQLAlchemy database model.

    This feature is coming in v0.2.0. Currently in preview mode.
    Creates a database model that inherits from reroute.db.models.Model.

    Examples:
        reroute create dbmodel --name User
        reroute create dbmodel --name Product
    """
    from reroute import FEATURE_FLAGS

    # Check feature flag
    if not FEATURE_FLAGS.get("dbmodel_command", False):
        click.secho("\n" + "="*50, fg='yellow', bold=True)
        click.secho("[PREVIEW] DBModel Command", fg='yellow', bold=True)
        click.secho("="*50, fg='yellow')
        click.secho("\nThis feature is coming in v0.2.0!", fg='cyan', bold=True)
        click.secho("\nWhat it will do:", fg='white')
        click.secho("  - Generate SQLAlchemy models with common fields", fg='white')
        click.secho("  - Inherit from reroute.db.models.Model base class", fg='white')
        click.secho("  - Include id, created_at, updated_at automatically", fg='white')
        click.secho("  - Support relationships and custom fields", fg='white')
        click.secho("\nPlanned usage:", fg='white')
        click.secho("  reroute create dbmodel --name User", fg='green')
        click.secho("  reroute create dbmodel --name Product", fg='green')
        click.secho("\nStay tuned for the v0.2.0 release!", fg='magenta', bold=True)
        click.echo()
        return

    # Feature implementation (for v0.2.0)
    click.secho("\n" + "="*50, fg='cyan', bold=True)
    click.secho("Generating Database Model", fg='cyan', bold=True)
    click.secho("="*50 + "\n", fg='cyan', bold=True)

    try:
        # Validate we're in a REROUTE project
        if not is_reroute_project():
            click.secho("[ERROR] Not in a REROUTE project directory!", fg='red', bold=True)
            click.secho("Run 'reroute init' first to create a project.", fg='yellow')
            sys.exit(1)

        # Prompt for name if not provided
        if name is None:
            def validate_model_name(text):
                """Real-time validation for model name"""
                if not text or not text.strip():
                    return False
                text = text.strip()
                text_no_underscore = text.lstrip('_')
                if not text_no_underscore:
                    return False
                if not text_no_underscore[0].isalpha():
                    return False
                if not re.match(r'^[a-zA-Z0-9_]+$', text):
                    return False
                return True

            name = inquirer.text(
                message="Model name (e.g., User or Product):",
                validate=validate_model_name,
                invalid_message="Model name must start with a letter and contain only letters, numbers, underscores."
            ).execute()

        # Create db_models directory if it doesn't exist
        db_models_dir = Path.cwd() / "app" / "db_models"
        db_models_dir.mkdir(parents=True, exist_ok=True)

        # Create __init__.py in db_models directory if it doesn't exist
        init_file = db_models_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""Database Models package"""\n')

        # Generate model file
        class_name = to_pascal_case(name)
        table_name = name.lower() + "s"  # Simple pluralization
        model_filename = name.lower() + ".py"
        model_file = db_models_dir / model_filename

        # Check if file already exists
        if model_file.exists():
            click.secho(f"[ERROR] Model file already exists: {model_file}", fg='red', bold=True)
            click.secho("Delete the existing file or choose a different name.", fg='yellow')
            sys.exit(1)

        # Render template
        template = jinja_env.get_template('models/db_model.py.j2')
        content = template.render(
            model_name=class_name,
            table_name=table_name,
            description=f"{class_name} database model",
            fields=[
                {"name": "name", "type": "String(100)", "nullable": False, "unique": False, "index": False},
                {"name": "email", "type": "String(255)", "nullable": True, "unique": True, "index": True},
            ]
        )

        # Write model file
        model_file.write_text(content)

        click.secho(f"[OK] Database model created: ", fg='green', bold=True, nl=False)
        click.secho(f"{model_file}", fg='cyan')
        click.secho(f"     Model: ", fg='blue', nl=False)
        click.secho(f"{class_name}", fg='green', bold=True)
        click.secho(f"     Table: ", fg='blue', nl=False)
        click.secho(f"{table_name}", fg='yellow')
        click.secho(f"     Inherits: ", fg='blue', nl=False)
        click.secho("reroute.db.models.Model", fg='magenta')

        click.secho(f"\n[TIP] Import with: ", fg='blue', nl=False)
        click.secho(f"from app.db_models.{name.lower()} import {class_name}", fg='cyan')

        click.secho(f"\n[NOTE] Customize fields in the generated file.", fg='yellow')
        click.secho("       Common types: String, Integer, Boolean, Text, DateTime, JSON", fg='white')

        click.echo()

    except Exception as e:
        click.secho(f"\n[ERROR] Failed to generate database model: {e}", fg='red', bold=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


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


@create.command(name='auth', hidden=True)
@click.option('--method', '-m', default='jwt',
              type=click.Choice(['jwt'], case_sensitive=False),
              help='Authentication method (jwt)')
def create_auth(method):
    """
    [PREVIEW] Create authentication scaffolding.

    This feature is coming in v0.2.0. Currently in preview mode.
    Generates JWT authentication with login, register, refresh, and profile routes.

    Examples:
        reroute create auth --method jwt
        reroute create auth -m jwt
    """
    import secrets
    from reroute import FEATURE_FLAGS

    # Check feature flag
    if not FEATURE_FLAGS.get("auth_scaffolding", False):
        click.secho("\n" + "="*50, fg='yellow', bold=True)
        click.secho("[PREVIEW] Auth Scaffolding", fg='yellow', bold=True)
        click.secho("="*50, fg='yellow')
        click.secho("\nThis feature is coming in v0.2.0!", fg='cyan', bold=True)
        click.secho("\nWhat it will generate:", fg='white')
        click.secho("  - app/auth/ module (jwt.py, password.py)", fg='white')
        click.secho("  - app/models/auth.py (Pydantic schemas)", fg='white')
        click.secho("  - app/routes/auth/ routes:", fg='white')
        click.secho("    - POST /auth/login", fg='green')
        click.secho("    - POST /auth/register", fg='green')
        click.secho("    - POST /auth/refresh", fg='green')
        click.secho("    - GET /auth/me (protected)", fg='green')
        click.secho("  - JWT config in config.py", fg='white')
        click.secho("\nPlanned usage:", fg='white')
        click.secho("  reroute create auth --method jwt", fg='green')
        click.secho("\nStay tuned for the v0.2.0 release!", fg='magenta', bold=True)
        click.echo()
        return

    # Feature implementation (for v0.2.0)
    click.secho("\n" + "="*50, fg='cyan', bold=True)
    click.secho("Generating Auth Scaffolding", fg='cyan', bold=True)
    click.secho("="*50 + "\n", fg='cyan', bold=True)

    try:
        # Validate we're in a REROUTE project
        if not is_reroute_project():
            click.secho("[ERROR] Not in a REROUTE project directory!", fg='red', bold=True)
            click.secho("Run 'reroute init' first to create a project.", fg='yellow')
            sys.exit(1)

        # Generate secure JWT secret
        jwt_secret = secrets.token_hex(32)

        # Create directories
        auth_dir = Path.cwd() / "app" / "auth"
        models_dir = Path.cwd() / "app" / "models"
        routes_auth_dir = Path.cwd() / "app" / "routes" / "auth"

        auth_dir.mkdir(parents=True, exist_ok=True)
        models_dir.mkdir(parents=True, exist_ok=True)

        click.secho("  Creating auth module...", fg='blue')

        # Generate auth/__init__.py
        init_template = jinja_env.get_template('auth/__init__.py.j2')
        (auth_dir / "__init__.py").write_text(init_template.render())
        click.secho("  [ OK ] app/auth/__init__.py", fg='green')

        # Generate auth/jwt.py
        jwt_template = jinja_env.get_template('auth/jwt.py.j2')
        (auth_dir / "jwt.py").write_text(jwt_template.render())
        click.secho("  [ OK ] app/auth/jwt.py", fg='green')

        # Generate auth/password.py
        password_template = jinja_env.get_template('auth/password.py.j2')
        (auth_dir / "password.py").write_text(password_template.render())
        click.secho("  [ OK ] app/auth/password.py", fg='green')

        click.secho("\n  Creating auth models...", fg='blue')

        # Create models __init__.py if not exists
        models_init = models_dir / "__init__.py"
        if not models_init.exists():
            models_init.write_text('"""Models package"""\n')

        # Generate models/auth.py
        models_template = jinja_env.get_template('auth/models.py.j2')
        (models_dir / "auth.py").write_text(models_template.render())
        click.secho("  [ OK ] app/models/auth.py", fg='green')

        click.secho("\n  Creating auth routes...", fg='blue')

        # Create route directories and files
        route_configs = [
            ("login", "login.py.j2", "POST /auth/login"),
            ("register", "register.py.j2", "POST /auth/register"),
            ("refresh", "refresh.py.j2", "POST /auth/refresh"),
            ("me", "me.py.j2", "GET /auth/me"),
        ]

        for route_name, template_name, endpoint in route_configs:
            route_dir = routes_auth_dir / route_name
            route_dir.mkdir(parents=True, exist_ok=True)

            template = jinja_env.get_template(f'routes/auth/{template_name}')
            (route_dir / "page.py").write_text(template.render())
            click.secho(f"  [ OK ] {endpoint}", fg='green')

        # Update config.py with JWT settings
        click.secho("\n  Updating configuration...", fg='blue')

        config_file = Path.cwd() / "config.py"
        if config_file.exists():
            config_content = config_file.read_text()

            # Check if JWT config already exists
            if "class JWT:" not in config_content:
                # Find the position to insert (after OpenAPI class or before the last class method)
                jwt_config = jinja_env.get_template('auth/config_jwt.py.j2').render(jwt_secret=jwt_secret)

                # Insert after OpenAPI class or at the end of AppConfig
                if "class OpenAPI:" in config_content:
                    # Find end of OpenAPI class and insert after
                    lines = config_content.split('\n')
                    insert_idx = None
                    in_openapi = False
                    indent_level = 0

                    for i, line in enumerate(lines):
                        if "class OpenAPI:" in line:
                            in_openapi = True
                            indent_level = len(line) - len(line.lstrip())
                        elif in_openapi and line.strip() and not line.startswith(' ' * (indent_level + 4)):
                            if line.strip() and not line.strip().startswith('#'):
                                insert_idx = i
                                break

                    if insert_idx:
                        lines.insert(insert_idx, "\n" + jwt_config)
                        config_content = '\n'.join(lines)
                        config_file.write_text(config_content)
                        click.secho("  [ OK ] Added JWT config to config.py", fg='green')
                    else:
                        click.secho("  [WARN] Could not auto-insert JWT config. Add manually.", fg='yellow')
                else:
                    click.secho("  [WARN] Add JWT config to config.py manually.", fg='yellow')
            else:
                click.secho("  [INFO] JWT config already exists in config.py", fg='cyan')

        # Success message
        click.secho("\n" + "="*50, fg='green', bold=True)
        click.secho("[SUCCESS] Auth scaffolding created!", fg='green', bold=True)
        click.secho("="*50, fg='green')

        click.secho("\nGenerated files:", fg='white')
        click.secho("  - app/auth/__init__.py", fg='cyan')
        click.secho("  - app/auth/jwt.py", fg='cyan')
        click.secho("  - app/auth/password.py", fg='cyan')
        click.secho("  - app/models/auth.py", fg='cyan')
        click.secho("  - app/routes/auth/login/page.py", fg='cyan')
        click.secho("  - app/routes/auth/register/page.py", fg='cyan')
        click.secho("  - app/routes/auth/refresh/page.py", fg='cyan')
        click.secho("  - app/routes/auth/me/page.py", fg='cyan')

        click.secho("\nNext steps:", fg='yellow', bold=True)
        click.secho("  1. Install dependencies: pip install pyjwt bcrypt", fg='white')
        click.secho("  2. Update JWT.SECRET in config.py for production", fg='white')
        click.secho("  3. Implement database storage in route handlers", fg='white')
        click.secho("  4. Look for TODO(human) comments for customization", fg='white')

        click.echo()

    except Exception as e:
        click.secho(f"\n[ERROR] Failed to generate auth scaffolding: {e}", fg='red', bold=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


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
