# Contributing to REROUTE

Thank you for considering contributing to REROUTE! We welcome all contributions - big or small.

## 📚 Full Contributing Guide

**For detailed guidelines, please see the [Contributing Guide](https://cbsajan.github.io/reroute-docs/contributing/) in our documentation.**

This includes:
- Development setup and workflow
- Coding standards and style guide
- Testing requirements
- Pull request process
- Documentation guidelines

## Quick Start for Contributors

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/reroute.git
cd reroute
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode
pip install -e .

# Install development dependencies
pip install pytest pytest-asyncio httpx black flake8 python-dotenv
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bugfix-name
```

### 4. Make Changes

- Write code following PEP 8 style guide
- Add tests for new features
- Update documentation if needed
- Run tests: `pytest`
- Format code: `black reroute/`

### 5. Submit Pull Request

- Push your changes to your fork
- Open a pull request with a clear description
- Link any related issues

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors.

### Expected Behavior

- Be respectful and considerate
- Provide constructive feedback
- Focus on what's best for the project
- Show empathy towards other contributors

### Unacceptable Behavior

- Harassment or discriminatory language
- Personal attacks or trolling
- Publishing others' private information

## How to Contribute

### Reporting Bugs

Open an issue with:
- Clear title and description
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, REROUTE version)

### Suggesting Features

Open an issue describing:
- The feature and its use case
- Expected benefits
- Implementation ideas (optional)

### Contributing Code

Areas where contributions are especially welcome:
- Flask and Django adapter implementations
- Additional CLI commands
- Test coverage expansion
- Documentation improvements
- Bug fixes and performance optimizations

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=reroute

# Run specific test file
pytest tests/test_router.py
```

## Commit Message Format

```
type(scope): brief description

Longer explanation if needed.

Fixes #issue_number
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Example:**
```
feat(cli): add model generation command

Added 'reroute generate model' command to create Pydantic models
with 5 standard schemas (Base, Create, Update, InDB, Response).

Fixes #42
```

## Getting Help

- 📚 [Documentation](https://cbsajan.github.io/reroute-docs)
- 💬 [GitHub Discussions](https://github.com/cbsajan/reroute/discussions)
- 🐛 [Issue Tracker](https://github.com/cbsajan/reroute/issues)

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md (coming soon)
- Mentioned in release notes
- Credited in documentation

## License

By contributing to REROUTE, you agree that your contributions will be licensed under the Apache License 2.0.

---

Thank you for contributing to REROUTE! 🚀
