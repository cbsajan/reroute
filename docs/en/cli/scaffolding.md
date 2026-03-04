# Scaffolding

Learn about REROUTE's project structure and templates.

## Project Structure

When you run `reroute init`, you get:

```
my-project/
├── app/
│   └── routes/
│       └── hello/
│           └── page.py
├── main.py
├── requirements.txt
└── .gitignore
```

## Route Templates

### Basic Template

```python
from reroute import RouteBase

class HelloRoutes(RouteBase):
    def get(self):
        return {"message": "Hello"}
```

### Full Template

```python
from reroute import RouteBase
from reroute.decorators import rate_limit, cache

class FullRoutes(RouteBase):
    tag = "Custom Tag"

    def __init__(self):
        super().__init__()
        # Initialize state

    def before_request(self):
        # Pre-processing
        return None

    @cache(duration=60)
    def get(self):
        return {"data": "..."}

    @rate_limit("5/min")
    def post(self):
        return {"created": True}

    def after_request(self, response):
        # Post-processing
        return response

    def on_error(self, error):
        return {"error": str(error)}
```

## Template Customization

Templates are located in the REROUTE package installation:

```
<python-site-packages>/reroute/cli/templates/
├── class_route.py.j2      # Basic route template
├── crud_route.py.j2       # CRUD operations template
├── model.py.j2            # Pydantic model template
├── fastapi_app.py.j2      # Main FastAPI app
├── config.py.j2           # Configuration file
├── logger.py.j2           # Logger setup
├── test_fastapi.py.j2     # Test template
├── route.http.j2          # HTTP test file
└── crud.http.j2           # CRUD HTTP tests
```

### Customizing Templates

To customize templates:

1. **Locate your Python installation:**
   ```bash
   python -c "import reroute; print(reroute.__file__)"
   ```

2. **Navigate to templates:**
   ```bash
   cd <path-to-site-packages>/reroute/cli/templates/
   ```

3. **Edit `.j2` files** (Jinja2 templates)

!!! warning "Template Customization Warning"
    **Only modify templates if you understand Jinja2 and the template variables!**

    - Templates use Jinja2 syntax with variables like `{{ route_name }}`, `{{ class_name }}`, etc.
    - Incorrect modifications can corrupt the library and cause errors in code generation
    - Changes affect **ALL projects** using this REROUTE installation
    - If you're not familiar with Jinja2 templating, it's safer to:
        1. Generate files with default templates
        2. Manually edit the generated files after creation

    **Required Knowledge:**
    - Jinja2 template syntax
    - Template variables used by REROUTE CLI
    - Python code structure and imports

    **Breaking changes can cause:**
    - Invalid Python code generation
    - Import errors
    - Missing required variables
    - Syntax errors in generated files

**Alternative:** For project-specific customization, manually edit generated files after creation instead of modifying templates.
