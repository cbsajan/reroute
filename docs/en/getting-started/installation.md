# Installation

Learn how to install REROUTE in your Python project.

!!! info "Current Version"
    **Latest Release**: v0.3.0
    **Python Support**: 3.8, 3.9, 3.10, 3.11, 3.12
    **Package Manager**: uv (required)

## Requirements

- **Python**: 3.8 or higher
- **Package Manager**: uv (required as of v0.3.0)
- **Framework**: FastAPI

!!! info "Why uv only?"
    REROUTE v0.3.0+ exclusively uses [uv](https://github.com/astral-sh/uv) - an ultra-fast Python package manager written in Rust. It's 10-100x faster than pip and provides better dependency resolution.

## Install uv

If you don't have uv installed:

=== "macOS/Linux"

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "Windows"

    ```bash
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

=== "With pip (temporary)"

    ```bash
    pip install uv
    ```

    You can remove pip after installing uv.

## Basic Installation

Install REROUTE with FastAPI support:

```bash
uv pip install reroute[fastapi]
```

This includes:
- REROUTE core
- FastAPI
- Uvicorn (ASGI server)

## Project Installation (Recommended)

For new projects, use REROUTE CLI to create a project with modern tooling:

```bash
reroute init myapi
cd myapi
uv sync
uv run main.py
```

The CLI automatically creates a `pyproject.toml` with uv configuration.

## Development Installation

For contributing to REROUTE:

```bash
# Clone the repository
git clone https://github.com/cbsajan/reroute.git
cd reroute

# Create virtual environment with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with dev dependencies
uv pip install -e ".[dev]"
```

## Verify Installation

Check that REROUTE is installed correctly:

```bash
python -c "import reroute; print(reroute.__version__)"
```

Or use the CLI:

```bash
reroute --version
# Output: REROUTE CLI v0.3.0
```

!!! note "Update Notifications"
    REROUTE automatically checks for updates when you run CLI commands. You'll see a notification if a newer version is available.

## Update REROUTE

To update to the latest version:

```bash
uv pip install --upgrade reroute[fastapi]
```

Or in your project directory:

```bash
uv sync --upgrade
```

## Uninstall

To remove REROUTE:

```bash
uv pip uninstall reroute
```

Or remove from your `pyproject.toml` and run:

```bash
uv sync
```

## Migration from pip

!!! warning "Breaking Change in v0.3.0"
    If you were using pip with REROUTE v0.2.x:

    **Old way (v0.2.x):**
    ```bash
    pip install reroute[fastapi]
    pip install -r requirements.txt
    ```

    **New way (v0.3.0+):**
    ```bash
    uv pip install reroute[fastapi]
    uv sync  # Replaces pip install -r requirements.txt
    ```

    **Benefits:**
    - 10-100x faster installations
    - Better dependency resolution
    - Built-in virtual environment management
    - Modern `pyproject.toml` support

!!! tip "Converting existing projects"
    To migrate an existing project from pip to uv:

    ```bash
    # 1. Install uv
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # 2. In your project directory
    cd your-project
    uv venv
    source .venv/bin/activate

    # 3. Replace requirements.txt with pyproject.toml
    # REROUTE CLI can help with this:
    reroute init --convert-existing

    # 4. Install dependencies
    uv sync
    ```

## Next Steps

!!! tip "Watch the Demo"
    See REROUTE in action with our video tutorial:

    <video width="100%" height="auto" controls style="border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <source src="https://github.com/cbsajan/reroute/raw/refs/heads/main/assets/demo.mp4" type="video/mp4">
        Your browser does not support the video tag.
    </video>

**[Quick Start Guide](quickstart.md)** - Build your first app in 5 minutes
**[First Route](first-route.md)** - Create your first route
**[Installation Troubleshooting](../troubleshooting/installation.md)** - Common installation issues