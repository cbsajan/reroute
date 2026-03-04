# Contributing to REROUTE

Thank you for your interest in contributing to REROUTE! This document provides guidelines and instructions for contributing.

## Ways to Contribute

- Report bugs and issues
- Suggest new features
- Improve documentation
- Submit pull requests
- Write tutorials and examples

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/reroute.git
cd reroute
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=reroute

# Run specific test file
pytest tests/test_adapters.py
```

### Code Style

We use:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting

Format your code before committing:

```bash
# Format code
black reroute tests

# Sort imports
isort reroute tests

# Check linting
flake8 reroute tests
```

### Type Checking

```bash
# Run mypy type checker
mypy reroute
```

## Making Changes

### 1. Write Tests

Add tests for new features or bug fixes:

```python
# tests/test_your_feature.py
def test_new_feature():
    # Your test here
    assert True
```

### 2. Update Documentation

- Update docstrings
- Add examples to guides
- Update CHANGELOG.md

### 3. Commit Your Changes

Follow conventional commit format:

```bash
git commit -m "feat: add new decorator for timeouts"
git commit -m "fix: resolve caching issue in FastAPI adapter"
git commit -m "docs: improve quickstart guide"
```

Commit types:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test changes
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

## Submitting Changes

### 1. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 2. Create Pull Request

1. Go to the [REROUTE repository](https://github.com/cbsajan/reroute)
2. Click "New Pull Request"
3. Select your fork and branch
4. Fill out the PR template
5. Submit for review

### PR Guidelines

- Describe what your PR does
- Reference related issues
- Include screenshots for UI changes
- Ensure all tests pass
- Update documentation

## Code Review Process

1. Maintainers will review your PR
2. Address any requested changes
3. Once approved, your PR will be merged
4. Your contribution will be in the next release!

## Community Guidelines

- Be respectful and inclusive
- Help others learn and grow
- Follow the [Code of Conduct](https://github.com/cbsajan/reroute/blob/main/CODE_OF_CONDUCT.md)

## Need Help?

- Check [existing issues](https://github.com/cbsajan/reroute/issues)
- Ask questions in discussions
- Reach out to maintainers

## Recognition

Contributors are recognized in:

- CHANGELOG.md
- GitHub contributors page
- Release notes

Thank you for making REROUTE better!
