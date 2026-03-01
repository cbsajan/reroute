# Getting Started

**Welcome to REROUTE!**

---

Here's where you'll learn how to get started with **REROUTE** and build your first file-based routed API.

This tutorial will guide you through installation, your first route, and core concepts step by step.

## What is REROUTE?

REROUTE is a modern routing framework that brings Next.js-style file-based routing to Python web frameworks. Instead of manually registering routes, you organize them in folders and files - REROUTE handles the rest.

## Prerequisites

- Python 3.8 or higher
- A web framework (FastAPI or Flask)
- Basic understanding of REST APIs

## Installation Options

### From PyPI (Recommended)

```bash
pip install reroute
```

### With specific framework support

=== "FastAPI"
    ```bash
    pip install reroute[fastapi]
    ```

=== "Flask"
    ```bash
    pip install reroute[flask]
    ```

=== "All frameworks"
    ```bash
    pip install reroute[all]
    ```

### From Source

```bash
git clone https://github.com/cbsajan/reroute.git
cd reroute
pip install -e .
```

## Next Steps

<div class="grid cards" markdown>

-   **Quick Start**

    ---

    Build your first REROUTE app in 5 minutes.

    [:octicons-arrow-right-24: Quick Start](quickstart.md)

-   **First Route**

    ---

    Create your first file-based route.

    [:octicons-arrow-right-24: First Route](first-route.md)

</div>
