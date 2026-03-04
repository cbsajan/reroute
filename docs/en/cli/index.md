# CLI

REROUTE includes a command-line interface for scaffolding and managing your file-based routes.

## Installation

The CLI is installed automatically with REROUTE:

```bash
pip install reroute
```

Verify installation:

```bash
reroute --version
```

## Quick Start

### Create a New Project

```bash
reroute init my-project --framework fastapi
cd my-project
```

### Create a Route

```bash
reroute create route --path /user --name User
```

This creates `app/routes/user/page.py` with boilerplate code.

### Create a Nested Route

```bash
reroute create route --path /user/profile --name UserProfile
```

Creates `app/routes/user/profile/page.py`.

## Available Commands

<div class="grid cards" markdown>

-   :material-plus-circle: [**init**](commands.md#init)

    ---

    Create a new REROUTE project with FastAPI/Flask

-   :material-file-plus: [**create route**](commands.md#generate-route-create-route)

    ---

    Generate a new route file with HTTP methods

-   :material-table: [**create crud**](commands.md#generate-crud-create-crud)

    ---

    Generate full CRUD operations (Create, Read, Update, Delete)

-   :material-code-braces: [**create model**](commands.md#generate-model-create-model)

    ---

    Generate Pydantic models for data validation

</div>

## CLI Options

Global options:

- `-V, --version` - Show REROUTE version and exit
- `--help` - Show help message and exit

All commands also support `--help` to show command-specific help.

## Examples

### Initialize with FastAPI

```bash
reroute init my-api --framework fastapi
```

### Initialize with Flask

```bash
reroute init my-app --framework flask
```

### Create Multiple Routes

```bash
reroute create route --path /user --name User
reroute create route --path /product --name Product
reroute create route --path /order --name Order
```

### Create with Custom Methods

```bash
reroute create route --path /user --name User --methods GET,POST,PUT,DELETE
```

## Interactive Mode

The CLI features an interactive mode with auto-completion:

```bash
reroute
```

Navigate through options with arrow keys and select with Enter.

## Configuration

CLI behavior can be customized via `.rerouterc` file:

```json
{
  "default_framework": "fastapi",
  "routes_dir": "app/routes",
  "template_style": "minimal"
}
```

## Troubleshooting

### Problem 1: Command not found: reroute

**Error:**
```bash
bash: reroute: command not found
```

**Solutions:**
1. Install REROUTE: `pip install reroute`
2. Ensure pip bin directory is in PATH:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"  # Linux/Mac
   ```
3. Use python module syntax: `python -m reroute --version`

### Problem 2: Invalid value for '--path': Path cannot contain invalid character

**Error:**
```
Error: Invalid value for '--path': Path cannot contain invalid character: :
```

**Cause:**
Trying to use `:id` syntax in path (not supported on Windows)

**Solution:**
Use query parameters instead of path parameters in folder names:
```bash
# Wrong:
reroute create route --path /users/:id

# Correct:
reroute create route --path /users --name Users
# Then use query parameter: user_id: int = Query(...)
```

### Problem 3: Not in a REROUTE project directory

**Error:**
```
[ERROR] Not in a REROUTE project directory!
Run 'reroute init' first to create a project.
```

**Solution:**
1. Initialize a project first: `reroute init my-api`
2. Navigate into the project: `cd my-api`
3. Then run other commands: `reroute create route --path /users --name Users`

### Problem 4: Class already exists error

**Error:**
```
[ERROR] Class 'Users' already exists in app/routes/users/page.py!
```

**Cause:**
Trying to create a route with a class name that already exists

**Solutions:**
1. Use a different name: `reroute create route --path /users --name UserRoutes`
2. Delete the existing route file first
3. Use `--methods` to add methods to existing route

### Problem 5: Generated code has incorrect imports

**Symptom:**
Generated code imports from `fastapi` instead of `reroute.params`

**Solution:**
Update REROUTE to the latest version:
```bash
pip install --upgrade reroute
```

Templates were fixed in v0.1.4 to use cross-framework imports.

## Learn More

- [Command Reference](commands.md) - Detailed command documentation
- [Scaffolding](scaffolding.md) - Project structure and templates
