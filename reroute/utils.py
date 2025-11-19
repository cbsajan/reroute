"""
REROUTE Utility Functions

Helper functions for the REROUTE framework.
"""

import socket
import sys
from typing import Optional, Type


def check_port_available(host: str, port: int) -> bool:
    """
    Check if a port is available for binding.

    Args:
        host: Host address to check
        port: Port number to check

    Returns:
        True if port is available, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            return True
    except OSError:
        return False


def ensure_port_available(host: str, port: int, exit_on_fail: bool = True) -> bool:
    """
    Ensure a port is available, with optional error handling.

    Args:
        host: Host address to check
        port: Port number to check
        exit_on_fail: If True, exit the program if port is unavailable

    Returns:
        True if port is available

    Raises:
        SystemExit: If port is unavailable and exit_on_fail is True
    """
    if not check_port_available(host, port):
        print("\n" + "="*50)
        print(f"ERROR: Port {port} is already in use!")
        print("="*50)
        print(f"\nPlease either:")
        print(f"  1. Stop the process using port {port}")
        print(f"  2. Change the PORT in config.py")
        print("\n")

        if exit_on_fail:
            sys.exit(1)
        return False

    return True


def run_server(
    app_module: str,
    config,
    project_name: Optional[str] = None,
    **uvicorn_kwargs
):
    """
    Run the REROUTE application server.

    This is a convenience wrapper around uvicorn.run() that:
    - Checks port availability
    - Shows formatted startup messages
    - Passes configuration to uvicorn

    Args:
        app_module: Module path to app (e.g., "main:app")
        config: Config class with HOST, PORT, AUTO_RELOAD settings
        project_name: Optional project name for display
        **uvicorn_kwargs: Additional arguments to pass to uvicorn.run()

    Example:
        from reroute import run_server
        from config import AppConfig

        if __name__ == "__main__":
            run_server("main:app", AppConfig, project_name="MyAPI")
    """
    import uvicorn

    # Get configuration
    HOST = getattr(config, 'HOST', '0.0.0.0')
    PORT = getattr(config, 'PORT', 8000)
    RELOAD = getattr(config, 'AUTO_RELOAD', False)

    # Check port availability
    ensure_port_available(HOST, PORT)

    # Display startup banner
    display_name = project_name or "REROUTE Application"
    print("\n" + "="*50)
    print(f"{display_name} - REROUTE + FastAPI")
    print("="*50)
    print("\nStarting server...")
    print(f"API Docs: http://localhost:{PORT}/docs")
    print(f"Health Check: http://localhost:{PORT}/health")
    print("\n")

    # Merge uvicorn arguments
    uvicorn_config = {
        "host": HOST,
        "port": PORT,
        "reload": RELOAD,
        **uvicorn_kwargs
    }

    # Start server
    uvicorn.run(app_module, **uvicorn_config)
