# Contributing to REROUTE

Thank you for considering contributing to REROUTE! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Documentation](#documentation)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, background, or identity.

### Expected Behavior

- Be respectful and considerate
- Provide constructive feedback
- Focus on what's best for the project
- Show empathy towards other contributors

### Unacceptable Behavior

- Harassment or discriminatory language
- Personal attacks
- Trolling or insulting comments
- Publishing others' private information

---

## How Can I Contribute?

### Reporting Bugs

Before creating a bug report:
1. Check existing issues to avoid duplicates
2. Use the latest version of REROUTE
3. Collect relevant information (OS, Python version, error messages)

When creating a bug report, include:
- **Clear title** describing the issue
- **Steps to reproduce** the bug
- **Expected behavior** vs actual behavior
- **Environment details** (OS, Python version, REROUTE version)
- **Error messages** or logs
- **Screenshots** if applicable

### Suggesting Features

Feature suggestions are welcome! Please:
1. Check if the feature has already been suggested
2. Provide a clear description of the feature
3. Explain the use case and benefits
4. Consider implementation complexity

### Contributing Code

Areas where contributions are especially welcome:
- **Flask adapter** implementation
- **Additional CLI commands**
- **Template improvements**
- **Test coverage** expansion
- **Documentation** improvements
- **Bug fixes**
- **Performance optimizations**

---

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- pip

### Setup Steps

1. **Fork the repository**
   ```bash
   # Click "Fork" on GitHub
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/cbsajan/reroute.git
   cd reroute
   ```

3. **Create virtual environment**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

4. **Install in editable mode**
   ```bash
   pip install -e .
   ```

5. **Install development dependencies**
   ```bash
   pip install pytest pytest-asyncio httpx black flake8
   ```

6. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bugfix-name
   ```

---

## Project Structure

```
reroute/
├── reroute/
│   ├── __init__.py           # Package exports
│   ├── config.py             # Configuration classes
│   ├── utils.py              # Utility functions
│   ├── core/
│   │   ├── router.py         # Route discovery
│   │   ├── loader.py         # Route loading
│   │   └── base.py           # RouteBase class
│   ├── adapters/
│   │   ├── fastapi.py        # FastAPI adapter
│   │   └── flask.py          # Flask adapter (TODO)
│   └── cli/
│       ├── commands.py       # CLI commands
│       └── templates/        # Jinja2 templates
│           ├── class_route.py.j2
│           ├── crud_route.py.j2
│           ├── fastapi_app.py.j2
│           ├── config.py.j2
│           └── test_fastapi.py.j2
├── tests/                    # Test files
├── docs/                     # Documentation
├── setup.py                  # Package setup
├── pyproject.toml           # Project metadata
└── README.md                # Main documentation
```

### Key Components

- **`reroute/core/`** - Core routing logic
- **`reroute/adapters/`** - Framework integrations
- **`reroute/cli/`** - CLI commands and templates
- **`reroute/config.py`** - Configuration system
- **`reroute/utils.py`** - Helper utilities

---

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:
- Line length: 100 characters (not 79)
- Use 4 spaces for indentation
- Use double quotes for strings

### Code Formatting

Use `black` for automatic formatting:
```bash
black reroute/
```

### Linting

Use `flake8` for linting:
```bash
flake8 reroute/ --max-line-length=100
```

### Type Hints

Use type hints where appropriate:
```python
def create_route(path: str, name: str) -> Path:
    """Create a route directory."""
    ...
```

### Docstrings

Use Google-style docstrings:
```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of function.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is invalid
    """
    ...
```

### Naming Conventions

- **Functions/methods**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_CASE`
- **Private members**: `_leading_underscore`

---

## Commit Guidelines

### Commit Message Format

```
type(scope): brief description

Longer explanation if needed.

Fixes #issue_number
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```bash
feat(cli): add interactive project name validation

Added validation for project names to prevent invalid characters
and reserved names.

Fixes #42
```

```bash
fix(fastapi): resolve docstring not showing in API docs

Fixed issue where route docstrings weren't being copied to
FastAPI wrapper functions.
```

```bash
docs(readme): update installation instructions
```

---

## Pull Request Process

### Before Submitting

1. **Test your changes** thoroughly
2. **Update documentation** if needed
3. **Add tests** for new features
4. **Run linting** and fix issues
5. **Update CHANGELOG** if applicable

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages follow guidelines
- [ ] No merge conflicts
- [ ] PR description explains changes

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Related Issues
Fixes #issue_number

## Screenshots (if applicable)
```

### Review Process

1. A maintainer will review your PR
2. Address any feedback or requested changes
3. Once approved, a maintainer will merge

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_router.py

# Run with coverage
pytest --cov=reroute
```

### Writing Tests

Place tests in the `tests/` directory:

```python
import pytest
from reroute.core.router import Router

def test_route_discovery():
    """Test route discovery functionality."""
    router = Router(app_dir="./test_app")
    routes = router.discover_routes()
    assert len(routes) > 0
```

### Test Coverage

- Aim for 80%+ coverage for new code
- Test edge cases and error conditions
- Test both success and failure paths

---

## Documentation

### Types of Documentation

1. **Code comments** - For complex logic
2. **Docstrings** - For all public functions/classes
3. **README.md** - Project overview
4. **docs/** - Detailed guides
5. **Inline examples** - In docstrings

### Documentation Guidelines

- Keep it clear and concise
- Use examples where helpful
- Update docs when changing functionality
- Check for typos and grammar

### Building Documentation

Documentation files:
- `README.md` - Main overview
- `docs/COMMANDS.md` - CLI reference
- `docs/CONTRIBUTING.md` - This file

---

## Specific Contribution Areas

### Adding a New Adapter

To add support for a new framework:

1. Create `reroute/adapters/framework_name.py`
2. Implement adapter class similar to `FastAPIAdapter`
3. Add template in `reroute/cli/templates/`
4. Update CLI to support new framework
5. Add tests
6. Update documentation

### Adding CLI Commands

To add a new CLI command:

1. Add command to `reroute/cli/commands.py`
2. Create any needed templates in `cli/templates/`
3. Add tests for the command
4. Update `docs/COMMANDS.md`

### Improving Templates

Templates are in `reroute/cli/templates/`:
- Use Jinja2 syntax
- Keep templates minimal and clean
- Test template rendering
- Update relevant documentation

---

## Getting Help

### Questions?

- Check existing issues and discussions
- Ask in GitHub Discussions
- Contact maintainers

### Resources

- [Python Style Guide](https://pep8.org/)
- [Git Commit Guidelines](https://www.conventionalcommits.org/)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)

---

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

---

## License

By contributing to REROUTE, you agree that your contributions will be licensed under the Apache License 2.0.

---

Thank you for contributing to REROUTE!
