# REROUTE CLI Templates

Organized Jinja2 templates for code generation.

## 📁 Structure

```
templates/
├── project/          # Project initialization
│   ├── env.example.j2       - Environment variables template
│   ├── gitignore.j2         - Git ignore file
│   └── requirements.txt.j2  - Python dependencies
│
├── config/           # Configuration files
│   ├── config.py.j2         - REROUTE configuration
│   └── logger.py.j2         - Logging setup
│
├── app/              # Main application
│   └── fastapi_app.py.j2    - FastAPI main app
│
├── routes/           # Route templates
│   ├── class_route.py.j2    - Basic route class
│   └── crud_route.py.j2     - CRUD route with all operations
│
├── models/           # Data models
│   ├── model.py.j2          - Pydantic model (validation)
│   └── db_model.py.j2       - SQLAlchemy model (database)
│
├── http/             # HTTP test files
│   ├── route.http.j2        - Basic route tests
│   └── crud.http.j2         - CRUD operation tests
│
└── tests/            # Test templates
    └── test_fastapi.py.j2   - FastAPI test suite
```

## 🎯 Usage in Code

```python
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

# Setup Jinja2 environment
TEMPLATES_DIR = Path(__file__).parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

# Load template from organized structure
template = jinja_env.get_template("project/env.example.j2")
content = template.render(
    project_name="myapi",
    db_type="postgresql",
    db_url="postgresql://user:pass@localhost/mydb"
)
```

## 📝 Template Variables

### Project Templates

**env.example.j2:**
- `project_name` - Project name
- `db_type` - Database type (postgresql, mysql, mongodb, sqlite)
- `db_url` - Database connection URL

**gitignore.j2:**
- `db_type` - Database type (adds DB-specific ignores)

**requirements.txt.j2:**
- `framework` - Web framework (fastapi, flask)
- `db_type` - Database type
- `include_tests` - Boolean for test dependencies

### Config Templates

**config.py.j2:**
- `config_type` - Configuration type (dev, prod)
- `host` - Server host
- `port` - Server port

**logger.py.j2:**
- `project_name` - Project name

### App Templates

**fastapi_app.py.j2:**
- `project_name` - Project name
- `description` - API description
- `config_type` - Configuration type
- `host` - Server host
- `port` - Server port

### Route Templates

**class_route.py.j2:**
- `class_name` - Route class name
- `route_path` - URL path
- `methods` - HTTP methods list

**crud_route.py.j2:**
- `model_name` - Model name (e.g., User)
- `route_path` - Base URL path

### Model Templates

**model.py.j2:**
- `model_name` - Model name

**db_model.py.j2:**
- `model_name` - Model name
- `table_name` - Database table name
- `description` - Model description
- `fields` - List of field definitions

### HTTP Test Templates

**route.http.j2:**
- `route_path` - URL path
- `methods` - HTTP methods to test

**crud.http.j2:**
- `route_path` - Base URL path
- `model_name` - Model name

### Test Templates

**test_fastapi.py.j2:**
- `framework` - Web framework

## 🔧 Adding New Templates

1. Create template file in appropriate subfolder
2. Use `.j2` extension
3. Add template variables documentation here
4. Update code to use new template path

## 📚 Jinja2 Syntax

- `{{ variable }}` - Variable substitution
- `{% if condition %}...{% endif %}` - Conditional
- `{% for item in list %}...{% endfor %}` - Loop
- `{# comment #}` - Comments

---

**Last Updated:** 2025-01-21
**Status:** Organized and Production Ready
