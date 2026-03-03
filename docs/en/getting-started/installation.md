# Installation

Learn how to install REROUTE in your Python project.

!!! info "Current Version"
    **Latest Release**: v0.2.5
    **Python Support**: 3.8, 3.9, 3.10, 3.11, 3.12

## Requirements

- **Python**: 3.8 or higher
- **Framework**: FastAPI

## Basic Installation

=== "pip"

    ```bash
    pip install reroute
    ```

    This installs the core REROUTE package without framework dependencies.

=== "uv (Recommended)"

    ```bash
    uv pip install reroute
    ```

    [uv](https://github.com/astral-sh/uv) is an ultra-fast Python package installer written in Rust. It's 10-100x faster than pip.

    **Install uv first:**
    ```bash
    # macOS/Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Windows
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

    # Or with pip
    pip install uv
    ```

!!! tip "Lazy Loading"
    REROUTE uses lazy imports for framework adapters. You only need to install the framework you're actually using.

!!! info "pyproject.toml Support"
    REROUTE projects include `pyproject.toml` for modern dependency management with uv.

## Framework-Specific Installation

Install REROUTE with FastAPI support:

=== "FastAPI (pip)"

    ```bash
    pip install reroute[fastapi]
    ```

    This includes FastAPI and Uvicorn.

=== "FastAPI (uv)"

    ```bash
    uv pip install reroute[fastapi]
    ```

    Faster installation with uv.


## Development Installation

For contributing to REROUTE:

=== "pip"

    ```bash
    # Clone the repository
    git clone https://github.com/cbsajan/reroute.git
    cd reroute

    # Create virtual environment
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

    # Install in editable mode with dev dependencies
    pip install -e ".[dev]"
    ```

=== "uv (Faster)"

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
# Output: REROUTE CLI v0.2.5
```

!!! note "Update Notifications"
    REROUTE automatically checks for updates when you run CLI commands. You'll see a notification if a newer version is available.

## Update REROUTE

To update to the latest version:

```bash
pip install --upgrade reroute[fastapi]
```

Or with uv:

```bash
uv pip install --upgrade reroute[fastapi]
```

## Uninstall

To remove REROUTE:

```bash
pip uninstall reroute
```

## Next Steps

!!! tip "Watch the Demo"
    See REROUTE in action with our 2-minute video tutorial:

    <video width="100%" height="auto" controls style="border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <source src="https://github.com/cbsajan/reroute/raw/main/reroute/assets/demo.mp4" type="video/mp4">
        Your browser does not support the video tag.
    </video>

    **[Quick Start Guide](quickstart.md)** - Build your first app in 5 minutes
    **[First Route](first-route.md)** - Create your first route
    **[Installation Troubleshooting](../troubleshooting/installation.md)** - Common installation issues
