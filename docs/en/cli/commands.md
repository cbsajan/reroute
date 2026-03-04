# CLI Commands

Complete reference for REROUTE CLI commands.

## init

Create a new REROUTE project.

```bash
reroute init [project-name] [OPTIONS]
```

### Options
- `--framework` - Framework to use (fastapi, flask)
- `--config` - Configuration type (dev, prod)
- `--host` - Server host (default: 0.0.0.0)
- `--port` - Server port (default: 7376)
- `--description` - Project description

### Example
```bash
reroute init my-api --framework fastapi --config dev
```

Interactive mode (no arguments):
```bash
reroute init
```

## generate / create

REROUTE provides two command groups for code generation:
- `reroute generate <type>` - Original command
- `reroute create <type>` - Alias (more intuitive)

Both work identically. Use whichever you prefer.

## generate route / create route

Generate a new route file.

```bash
reroute generate route [OPTIONS]
reroute create route [OPTIONS]
```

### Options
- `--path` - Route path (e.g., /users or /api/posts)
- `--name` - Route name (e.g., Users or Posts)
- `--methods` - HTTP methods (comma-separated, default: GET,POST,PUT,DELETE)
- `--http-test` - Generate HTTP test file

### Examples
```bash
# Interactive mode
reroute create route

# With options
reroute create route --path /users --name Users

# Nested route
reroute create route --path /api/v1/users --name Users

# With specific methods
reroute create route --path /users --name Users --methods GET,POST

# With HTTP test file
reroute create route --path /users --name Users --http-test
```

## generate crud / create crud

Generate a full CRUD route with Create, Read, Update, Delete operations.

```bash
reroute generate crud [OPTIONS]
reroute create crud [OPTIONS]
```

### Options
- `--path` - Route path (e.g., /users or /api/posts)
- `--name` - Resource name (singular, e.g., User or Post)
- `--http-test` - Generate HTTP test file

### Examples
```bash
# Interactive mode
reroute create crud

# With options
reroute create crud --path /users --name User

# With HTTP test file
reroute create crud --path /users --name User --http-test
```

### Generated CRUD Operations

The CRUD command generates a route with these operations:

| Method | Endpoint | Operation |
|--------|----------|-----------|
| GET | `/users` | List all users |
| POST | `/users` | Create new user |
| GET | `/users/:id` | Get user by ID |
| PUT | `/users/:id` | Update user |
| DELETE | `/users/:id` | Delete user |

## generate model / create model

Generate Pydantic models for data validation.

```bash
reroute generate model [OPTIONS]
reroute create model [OPTIONS]
```

### Options
- `--name` - Model name (singular, e.g., User or Post)

### Examples
```bash
# Interactive mode
reroute create model

# With name
reroute create model --name User
reroute generate model --name Post
```

### Generated Model Schemas

Creates 5 Pydantic model schemas in `app/models/<name>.py`:

| Schema | Purpose | Usage |
|--------|---------|-------|
| `ModelBase` | Base schema with common fields | Shared fields |
| `ModelCreate` | For POST requests | Creating resources |
| `ModelUpdate` | For PUT/PATCH requests | Updating (all fields optional) |
| `ModelInDB` | Database representation | With id, timestamps |
| `ModelResponse` | API response schema | GET requests |

### Example Output

```bash
$ reroute create model --name User

[OK] Model created: D:\project\app\models\user.py
     Model: User
     Schemas: UserBase, UserCreate, UserUpdate, UserInDB, UserResponse

[NOTE] Generated with default fields: name, description, is_active
[TIP] Customize the fields in the generated file to match your requirements.

[TIP] Import with: from app.models.user import UserCreate, UserResponse
```

### Using Generated Models

```python
from app.models.user import UserCreate, UserResponse
from reroute import RouteBase
from reroute.params import Body

class UsersRoutes(RouteBase):
    def post(self, user: UserCreate = Body(...)):
        # Automatic validation with Pydantic
        return {"user": user.model_dump()}
```

## db

Database management commands for migrations and versioning.

```bash
reroute db [COMMAND]
```

### Available Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize database migrations |
| `migrate` | Create a new migration |
| `upgrade` | Apply all pending migrations |
| `downgrade` | Rollback migrations |
| `current` | Show current migration version |
| `history` | Show migration history |

### Examples

```bash
# Initialize database
reroute db init

# Create a migration
reroute db migrate "Add users table"

# Apply migrations
reroute db upgrade

# Check current version
reroute db current

# View migration history
reroute db history

# Rollback last migration
reroute db downgrade
```

## version

Show REROUTE version.

```bash
reroute --version
```

## help

Show help for commands.

```bash
reroute --help
reroute <command> --help
```
