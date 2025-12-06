"""
Version Gating Utility for REROUTE

Provides reusable functions to gate features based on version requirements.
This allows for flexible feature management across different releases.
"""

from typing import Optional, Callable, Any
from packaging import version
import click


def is_version_enabled(
    current_version: str,
    min_version: Optional[str] = None,
    max_version: Optional[str] = None,
    enabled_versions: Optional[list] = None
) -> bool:
    """
    Check if a feature should be enabled based on version constraints.

    Args:
        current_version: Current REROUTE version (e.g., "0.2.0")
        min_version: Minimum version required (inclusive)
        max_version: Maximum version allowed (inclusive)
        enabled_versions: Specific list of enabled versions

    Returns:
        True if feature should be enabled, False otherwise

    Examples:
        # Enable from version 0.2.0 onwards
        is_version_enabled("0.2.0", min_version="0.2.0")

        # Enable only in specific versions
        is_version_enabled("0.2.0", enabled_versions=["0.2.0", "0.2.1"])

        # Enable between versions (inclusive)
        is_version_enabled("0.2.0", min_version="0.1.5", max_version="0.3.0")
    """
    current = version.parse(current_version)

    # Check enabled_versions first (explicit list)
    if enabled_versions is not None:
        return any(current == version.parse(v) for v in enabled_versions)

    # Check minimum version
    if min_version is not None:
        if current < version.parse(min_version):
            return False

    # Check maximum version
    if max_version is not None:
        if current > version.parse(max_version):
            return False

    return True


def gate_feature(
    feature_name: str,
    min_version: Optional[str] = None,
    max_version: Optional[str] = None,
    enabled_versions: Optional[list] = None,
    preview_message: Optional[str] = None
) -> Callable:
    """
    Decorator to gate CLI commands based on version requirements.

    Args:
        feature_name: Name of the feature for display
        min_version: Minimum version required
        max_version: Maximum version allowed
        enabled_versions: Specific list of enabled versions
        preview_message: Custom message to show when disabled

    Returns:
        Decorator function

    Example:
        @gate_feature("DB Models", min_version="0.3.0")
        @click.command()
        def create_dbmodel():
            # Command implementation
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Get current version
            from reroute import __version__

            # Check if feature is enabled
            if is_version_enabled(
                __version__,
                min_version=min_version,
                max_version=max_version,
                enabled_versions=enabled_versions
            ):
                # Feature is enabled, execute command
                return func(*args, **kwargs)
            else:
                # Feature is disabled, show preview message
                if preview_message:
                    message = preview_message
                else:
                    if min_version:
                        message = f"This feature will be available in REROUTE v{min_version} or later."
                    elif max_version:
                        message = f"This feature was available until REROUTE v{max_version}."
                    elif enabled_versions:
                        versions_str = ", ".join(enabled_versions)
                        message = f"This feature is only available in REROUTE versions: {versions_str}"
                    else:
                        message = "This feature is currently disabled."

                click.secho("\n" + "="*50, fg='yellow', bold=True)
                click.secho(f"[PREVIEW] {feature_name}", fg='yellow', bold=True)
                click.secho("="*50, fg='yellow')
                click.secho(f"\n{message}\n", fg='yellow')
                click.secho("Note: This is a preview of upcoming features.\n", fg='cyan')
                return

        return wrapper
    return decorator


def get_feature_status(
    feature_name: str,
    min_version: Optional[str] = None,
    max_version: Optional[str] = None,
    enabled_versions: Optional[list] = None
) -> dict:
    """
    Get detailed status information for a feature.

    Returns:
        Dictionary with status information
    """
    from reroute import __version__

    enabled = is_version_enabled(
        __version__,
        min_version=min_version,
        max_version=max_version,
        enabled_versions=enabled_versions
    )

    status = {
        "feature": feature_name,
        "current_version": __version__,
        "enabled": enabled,
        "min_version": min_version,
        "max_version": max_version,
        "enabled_versions": enabled_versions
    }

    return status


# Common version gates for REROUTE features
FEATURE_GATES = {
    "database_init": {
        "min_version": "0.2.0",
        "description": "Database setup in init command"
    },
    "dbmodel_command": {
        "min_version": "0.2.0",
        "description": "Database model generation command"
    },
    "auth_scaffolding": {
        "min_version": "0.3.0",  # Future feature
        "description": "Authentication scaffolding"
    },
    "graphql_support": {
        "enabled_versions": [],  # Not implemented yet
        "description": "GraphQL adapter support"
    }
}


def is_feature_enabled(feature_key: str) -> bool:
    """
    Quick check if a feature is enabled using FEATURE_GATES.

    Args:
        feature_key: Key from FEATURE_GATES dictionary

    Returns:
        True if feature is enabled
    """
    if feature_key not in FEATURE_GATES:
        return False

    gate_config = FEATURE_GATES[feature_key]

    from reroute import __version__

    return is_version_enabled(
        __version__,
        min_version=gate_config.get("min_version"),
        max_version=gate_config.get("max_version"),
        enabled_versions=gate_config.get("enabled_versions")
    )