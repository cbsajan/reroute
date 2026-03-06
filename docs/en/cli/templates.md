# Project Templates

REROUTE v0.4.0+ uses **Cookiecutter templates** for project scaffolding. Templates are maintained as separate GitHub repositories, enabling independent versioning and community contributions.

## Official Templates

### Base Template
**Repository**: [github.com/rerouteorg/reroute-base-template](https://github.com/rerouteorg/reroute-base-template)

A minimal FastAPI project with REROUTE file-based routing.

**Features:**
- FastAPI with REROUTE adapter
- Example CRUD route (`/hello`)
- Configuration management
- Logging setup
- Optional database support (PostgreSQL, MySQL, SQLite, MongoDB)
- Optional test suite
- UV package manager support

**Use when:**
- Starting a new API project
- Learning REROUTE basics
- Building a simple backend service

### Auth Template
**Repository**: [github.com/rerouteorg/reroute-auth-template](https://github.com/rerouteorg/reroute-auth-template)

Authentication-focused template with JWT-based user management.

**Features:**
- JWT authentication (access + refresh tokens)
- Secure password hashing (bcrypt)
- User registration endpoint
- Login endpoint
- Token refresh mechanism
- Protected user profile endpoint
- Database integration for user storage

**Endpoints:**
- `POST /auth/register` - Create new user account
- `POST /auth/login` - Authenticate and get tokens
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user profile (protected)

**Use when:**
- Building an API with user authentication
- Need JWT-based session management
- Starting a SaaS or multi-user application

## Usage

### Via REROUTE CLI (Recommended)

```bash
# Using built-in templates
reroute init myapi --template base
reroute init myauth --template auth

# With options
reroute init myapi --template base --database postgresql
reroute init myauth --template auth --database mongodb
```

### Via Cookiecutter Directly

```bash
# Install cookiecutter
pip install cookiecutter

# Use a template
cookiecutter gh:rerouteorg/reroute-base-template
cookiecutter gh:rerouteorg/reroute-auth-template
```

### Custom GitHub Templates

Use any Cookiecutter template from GitHub:

```bash
# Using a custom template
reroute init myproject --template gh:username/my-template

# Or directly with cookiecutter
cookiecutter gh:username/my-template
```

## Template Format

Templates must follow Cookiecutter conventions:

1. **cookiecutter.json** - Template configuration with variables
2. **{{cookiecutter.project_name}}/** - Project root directory
3. Template files use `{{cookiecutter.variable_name}}` for substitution

### Design Principle: Minimal User Configuration

**Rule**: If it's a REROUTE default, hardcode it in templates. If it's a user choice, put it in cookiecutter.json.

**Why?**
- **Cleaner user experience** - Users only see what they need to customize
- **Single source of truth** - REROUTE defaults defined once in templates
- **Easier maintenance** - Change default port? Edit one template file
- **Less confusion** - No framework internals exposed to users

### Unified Schema (v0.5.0+)

**REROUTE templates use a minimal 7-field schema** where framework defaults are hardcoded in templates, not exposed to users.

#### Base Template Schema

```json
{
  "project_name": "myapi",
  "description": "My API",
  "author_name": "Your Name",
  "author_email": "you@example.com",
  "include_tests": true,
  "include_database": false,
  "database_type": "none"
}
```

#### Auth Template Schema

```json
{
  "project_name": "my-auth-api",
  "description": "Authentication API",
  "author_name": "Your Name",
  "author_email": "you@example.com",
  "include_tests": true,
  "include_database": true,
  "database_type": "postgresql"
}
```

**Hardcoded REROUTE Defaults (not in cookiecutter.json):**
- Framework: `fastapi`
- Host: `0.0.0.0`
- Port: `7376`
- Reload: `false` (production mode)
- JWT Algorithm: `HS256`
- JWT Access Token Expiry: `30` minutes
- JWT Refresh Token Expiry: `7` days

### Template Requirements (v0.5.0+)

Templates can declare their requirements using the `_requirements` field. This field is prefixed with underscore to indicate it's metadata, not a user-configurable variable.

#### Requirement Types

```json
{
  "_requirements": {
    "database": "optional"  // or "required"
  }
}
```

#### Detailed Requirements with Messages

For better user experience, you can provide detailed requirements with custom messages:

```json
{
  "_requirements": {
    "database": {
      "type": "required",
      "message": "Auth template requires a database for user authentication"
    }
  }
}
```

#### Example: Auth Template with Requirements

```json
{
  "_requirements": {
    "database": {
      "type": "required",
      "message": "Auth template requires a database for user authentication"
    }
  },
  "project_name": "my-auth-api",
  "description": "Authentication API",
  "author_name": "Your Name",
  "author_email": "you@example.com",
  "include_tests": true,
  "include_database": true,
  "database_type": "postgresql"
}
```

#### Example: Base Template with Optional Database

```json
{
  "_requirements": {
    "database": "optional"
  },
  "project_name": "myapi",
  "description": "My API",
  "author_name": "Your Name",
  "author_email": "you@example.com",
  "include_tests": true,
  "include_database": false,
  "database_type": "none"
}
```

**How Requirements Work:**
- When `database` is `required`: CLI skips "Would you like to set up a database?" and asks "Which database?" directly
- When `database` is `optional`: CLI asks "Would you like to set up a database?" first
- Custom messages are shown before the database prompt for better context
- Requirements are validated before project creation to prevent broken templates

Example template file:

```python
# main.py
app = FastAPI(
    title="{{ cookiecutter.project_name }}",
    description="{{ cookiecutter.description }}"
)
```

## Creating Custom Templates

### 1. Create a Cookiecutter Template

```bash
mkdir my-reroute-template
cd my-reroute-template

# Create cookiecutter.json
cat > cookiecutter.json << EOF
{
  "project_name": "myapi",
  "description": "My API"
}
EOF

# Create template directory
mkdir "{{cookiecutter.project_name}}"
cd "{{cookiecutter.project_name}}"

# Add your template files
# main.py, config.py, etc.
```

### 2. Use Cookiecutter Syntax

In your template files, use `{{cookiecutter.variable_name}}`:

```python
# main.py
app = FastAPI(
    title="{{ cookiecutter.project_name }}",
    description="{{ cookiecutter.description }}"
)
```

**For REROUTE templates, hardcode framework defaults:**

```python
# config.py
class Config:
    # REROUTE defaults - hardcoded, not from cookiecutter
    HOST = "0.0.0.0"
    PORT = 7376
    AUTO_RELOAD = False

    # User-configurable values from cookiecutter.json
    PROJECT_NAME = "{{ cookiecutter.project_name }}"
    DESCRIPTION = "{{ cookiecutter.description }}"
    AUTHOR = "{{ cookiecutter.author_name }}"
```

Conditional blocks:

```python
# requirements.txt
fastapi
uvicorn
{% if cookiecutter.database_type != 'none' %}
python-dotenv
{% if cookiecutter.database_type == 'postgresql' %}
psycopg2-binary
sqlalchemy
alembic
{% endif %}
{% endif %}
```

**Important:** Use `database_type` instead of `database` for consistency.

### 3. Publish to GitHub

```bash
git init
git add .
git commit -m "Initial template"
gh repo create my-reroute-template --public
git push -u origin main
```

### 4. Use Your Template

```bash
reroute init myproject --template gh:username/my-reroute-template
```

## Template Best Practices

### Directory Structure

```
my-template/
├── cookiecutter.json          # Template configuration
├── README.md                  # Template documentation
├── LICENSE                    # Template license
└── {{cookiecutter.project_name}}/
    ├── app/                   # Application code
    ├── config.py              # Configuration
    ├── main.py                # Entry point
    └── ...
```

### Naming Convention

**Official REROUTE templates:** Use `reroute-*` format
- `reroute-base`
- `reroute-auth`
- `reroute-ecommerce`

**Community templates:** Use any name
- `my-awesome-starter`
- `company-api-template`

### Schema Migration Guide (v0.4.x → v0.5.0)

**What Changed:**
- Removed: `framework`, `host`, `port`, `reload`, `jwt_secret`, `jwt_algorithm`, `access_token_expire_minutes`, `refresh_token_expire_days`
- Added: `author_name`, `author_email`
- Changed: `database` → `database_type`
- Changed: `include_tests` from string ("Yes"/"No") to boolean (true/false)

**Migration Steps:**

1. **Update cookiecutter.json:**
```json
// OLD (v0.4.x)
{
  "project_name": "myapi",
  "framework": "fastapi",
  "host": "0.0.0.0",
  "port": 7376,
  "reload": true,
  "database": "postgresql"
}

// NEW (v0.5.0+)
{
  "project_name": "myapi",
  "description": "My API",
  "author_name": "Your Name",
  "author_email": "you@example.com",
  "include_tests": true,
  "include_database": true,
  "database_type": "postgresql"
}
```

2. **Hardcode defaults in config.py:**
```python
# Replace {{ cookiecutter.framework }}, {{ cookiecutter.host }}, {{ cookiecutter.port }}
# with hardcoded values
class Config:
    HOST = "0.0.0.0"
    PORT = 7376
    AUTO_RELOAD = False
```

3. **Update template conditionals:**
```python
# OLD
{% if cookiecutter.database == 'postgresql' %}

# NEW
{% if cookiecutter.database_type == 'postgresql' %}
```

### Security Considerations

1. **Never include secrets** in templates
2. **Use environment variables** for sensitive data
3. **Provide .env.example** files with clear comments
4. **Document security requirements**

Example (REROUTE auth template):
```python
# config.py
import os

class AuthConfig(Config):
    # REROUTE defaults - hardcoded
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7

    # User must provide this via environment variable
    SECRET = os.getenv("REROUTE_JWT_SECRET")
    if not SECRET:
        raise ValueError("REROUTE_JWT_SECRET environment variable not set!")
```

**.env.example:**
```bash
# REQUIRED: Generate secure secret
# python -c "import secrets; print(secrets.token_urlsafe(32))"
REROUTE_JWT_SECRET=CHANGE_THIS_SECRET
```

## Template Registry

REROUTE includes a built-in template registry for convenience:

```python
BUILTIN_TEMPLATES = {
    'base': 'gh:rerouteorg/reroute-base-template',
    'auth': 'gh:rerouteorg/reroute-auth-template',
}
```

This allows short names:
```bash
reroute init myapi --template base  # Uses gh:rerouteorg/reroute-base-template
```

## Community Templates

Want to share your template?

1. Create a Cookiecutter template
2. Add `reroute` topic on GitHub
3. Submit to REROUTE documentation for listing

We'll feature community templates that:
- Follow best practices
- Include documentation
- Are actively maintained
- Add unique value

## Migration from v0.3.x

### Breaking Changes in v0.4.0

1. **Templates no longer bundled** - Must fetch from GitHub
2. **Internet required** - `reroute init` needs GitHub access
3. **New `--template` flag** - Explicit template selection
4. **Jinja2 removed** - All template generation uses Cookiecutter

### Migration Guide

**v0.3.x (old):**
```bash
reroute init myapi
# Used embedded Jinja2 templates
```

**v0.4.0 (new):**
```bash
reroute init myapi --template base
# Fetches template from GitHub
```

**For equivalent results:**
- `--template base` = old default behavior
- `--template auth` = old `--auth` flag behavior

## Troubleshooting

### Template Not Found

```
Error: Template 'gh:user/repo' not found
```

**Solutions:**
1. Verify the GitHub repository exists
2. Check the repository is public
3. Ensure `cookiecutter.json` exists at the root

### Network Issues

```
Error: Could not fetch template
```

**Solutions:**
1. Check internet connection
2. Verify GitHub is accessible
3. Try using Cookiecutter directly to debug

### Variable Substitution Failed

```
Error: template variable not defined
```

**Solutions:**
1. Check `cookiecutter.json` has all required variables
2. Verify template syntax: `{{cookiecutter.variable_name}}`
3. Ensure no typos in variable names

## Resources

- [Cookiecutter Documentation](https://cookiecutter.readthedocs.io/)
- [Cookiecutter GitHub](https://github.com/cookiecutter/cookiecutter)
- [REROUTE Templates](https://github.com/rerouteorg/reroute-base-template)
