# REROUTE CLI Commands Reference

Complete guide to all REROUTE CLI commands and options.

## Table of Contents

- [Global Options](#global-options)
- [init - Initialize Project](#init---initialize-project)
- [generate route - Generate Route](#generate-route---generate-route)
- [generate crud - Generate CRUD Route](#generate-crud---generate-crud-route)

---

## Global Options

All REROUTE commands display a banner and use colored, interactive prompts with arrow-key navigation.

---

## init - Initialize Project

Create a new REROUTE project with complete folder structure, configuration, and example routes.

### Usage

```bash
# Interactive mode (recommended)
reroute init

# With project name
reroute init myapi

# With all options
reroute init myapi --framework fastapi --host 0.0.0.0 --port 7376
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `name` | No | Project name (prompted if not provided) |

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--framework` | choice | interactive | Backend framework: `fastapi` or `flask` |
| `--config` | choice | `dev` | Configuration type: `dev` or `prod` |
| `--host` | string | `0.0.0.0` | Server host address |
| `--port` | integer | `7376` | Server port number |
| `--description` | string | empty | Project description |

### Interactive Prompts

When run without arguments, the CLI will ask:

1. **Project name**: Validates for:
   - Non-empty name
   - Valid filesystem characters (letters, numbers, dash, underscore)
   - Not starting with dash or underscore
   - Not a reserved name
   - Directory doesn't already exist

2. **Framework selection**: Choose between FastAPI and Flask (arrow keys)

3. **Generate test cases**: Choose Yes/No (arrow keys)

4. **Configuration review**: Shows all settings and asks for confirmation

### Project Structure Created

```
myapi/
├── app/
│   ├── __init__.py
│   └── routes/
│       ├── __init__.py
│       └── hello/
│           └── page.py           # Example route
├── tests/                         # (if tests selected)
│   ├── __init__.py
│   └── test_main.py
├── config.py                      # Project configuration
├── main.py                        # Application entry point
└── requirements.txt               # Dependencies
```

### Examples

```bash
# Create project interactively
reroute init

# Create FastAPI project named "blog-api"
reroute init blog-api --framework fastapi

# Create project with custom port
reroute init shop-api --framework fastapi --port 3000

# Create production config project
reroute init prod-api --config prod
```

### Next Steps After Init

After creating a project:

```bash
cd myapi
pip install -r requirements.txt
python main.py
```

Visit `http://localhost:7376/docs` for API documentation.

---

## generate route - Generate Route

Generate a new route file with specified HTTP methods.

### Usage

```bash
# Interactive mode (recommended)
reroute generate route

# With all options
reroute generate route --path /users --name Users --methods GET,POST --http-test
```

### Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--path` | Yes | prompted | URL path (e.g., `/users` or `/api/posts`) |
| `--name` | Yes | prompted | Route name (e.g., `Users` or `Posts`) |
| `--methods` | No | `GET,POST,PUT,DELETE` | Comma-separated HTTP methods |
| `--http-test` | No | `False` | Generate `.http` test file |

### Requirements

- Must be run inside a REROUTE project (folder with `app/routes/`)
- Path can include nested routes (e.g., `/api/v1/users`)

### Generated Files

**Route File**: `app/routes/{path}/page.py`
- Contains class-based route with specified methods
- Includes docstrings for each method
- Methods: `get()`, `post()`, `put()`, `delete()` (based on `--methods`)

**HTTP Test File** (if `--http-test` flag used): `tests/{path}.http`
- Ready-to-use HTTP requests for testing
- One request per method

### Examples

```bash
# Generate /users route interactively
reroute generate route

# Generate /posts route with GET and POST only
reroute generate route --path /posts --name Posts --methods GET,POST

# Generate nested route with HTTP tests
reroute generate route --path /api/v1/products --name Products --http-test

# Generate admin route
reroute generate route --path /admin/settings --name AdminSettings
```

### Path Mapping

The `--path` option determines the folder structure:

| Path | Generated Folder |
|------|------------------|
| `/users` | `app/routes/users/` |
| `/api/posts` | `app/routes/api/posts/` |
| `/v1/products` | `app/routes/v1/products/` |

---

## generate crud - Generate CRUD Route

Generate a full CRUD (Create, Read, Update, Delete) route with all operations.

### Usage

```bash
# Interactive mode (recommended)
reroute generate crud

# With all options
reroute generate crud --path /users --name User --http-test
```

### Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--path` | Yes | prompted | URL path for the resource |
| `--name` | Yes | prompted | Resource name (singular, e.g., `User` not `Users`) |
| `--http-test` | No | `False` | Generate `.http` test file |

### Requirements

- Must be run inside a REROUTE project
- Name should be singular (e.g., `User`, not `Users`)

### Generated Files

**CRUD Route File**: `app/routes/{path}/page.py`
- `get()` - Get all resources
- `post()` - Create new resource
- `put()` - Update resource by ID
- `delete()` - Delete resource by ID
- Helper method `_find_by_id()` for ID-based operations

**HTTP Test File** (if `--http-test` flag used): `tests/{path}.http`
- Full CRUD operation examples
- Sample JSON payloads for POST/PUT

### Examples

```bash
# Generate CRUD for users
reroute generate crud --path /users --name User

# Generate CRUD for blog posts with tests
reroute generate crud --path /api/posts --name Post --http-test

# Generate CRUD for products
reroute generate crud --path /products --name Product

# Generate nested CRUD route
reroute generate crud --path /api/v1/categories --name Category --http-test
```

### CRUD Operations

Generated routes support these operations:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/users` | List all users |
| POST | `/users` | Create new user |
| PUT | `/users` | Update user by ID (from request body) |
| DELETE | `/users` | Delete user by ID (from request body) |

---

## Command Validation

### Project Name Validation (init)

Valid characters:
- Letters (a-z, A-Z)
- Numbers (0-9)
- Dash (-)
- Underscore (_)

Invalid:
- Cannot start with dash or underscore
- Cannot be a reserved name (con, prn, aux, nul, com1, lpt1, test, tests, etc.)
- Cannot be an existing directory

### Route Path Validation (generate)

- Must be run inside a REROUTE project
- Path can contain `/` for nested routes
- Path is automatically cleaned and converted to folder structure

---

## Tips

### Interactive vs Flag Mode

**Interactive Mode** (recommended for new users):
```bash
reroute init
reroute generate route
```

**Flag Mode** (faster for experienced users):
```bash
reroute init myapi --framework fastapi --port 7376
reroute generate route --path /users --name Users --http-test
```

### Using HTTP Test Files

When `--http-test` flag is used, `.http` files are generated in `tests/` folder.

Use with:
- VS Code REST Client extension
- IntelliJ HTTP Client
- Or any HTTP file runner

### Project Validation

Some commands require being in a REROUTE project. The CLI checks for:
- `app/routes/` directory exists
- Run commands from project root (where `main.py` is)

---

## Error Messages

Common error messages and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| `Project name is required!` | No name provided | Provide project name or use interactive mode |
| `Directory already exists` | Project folder exists | Use different name or delete existing folder |
| `Not in a REROUTE project directory!` | Wrong directory | Navigate to project root |
| `Project name can only contain...` | Invalid characters | Use only letters, numbers, dash, underscore |

---

## Examples Workflow

### Creating a Blog API

```bash
# 1. Initialize project
reroute init blog-api --framework fastapi

# 2. Navigate to project
cd blog-api

# 3. Generate posts CRUD
reroute generate crud --path /api/posts --name Post --http-test

# 4. Generate comments route
reroute generate route --path /api/comments --name Comments --methods GET,POST

# 5. Install dependencies
pip install -r requirements.txt

# 6. Run server
python main.py
```

### Creating an E-commerce API

```bash
# 1. Initialize
reroute init shop-api

# 2. Generate routes
reroute generate crud --path /api/products --name Product --http-test
reroute generate crud --path /api/orders --name Order --http-test
reroute generate route --path /api/cart --name Cart

# 3. Run
cd shop-api
pip install -r requirements.txt
python main.py
```

---

For more information, visit the [main documentation](../README.md).
