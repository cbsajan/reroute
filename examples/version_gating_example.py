"""
Example of using the new version gating system for future features.

This demonstrates how to gate features based on version requirements
for future REROUTE releases.
"""

from reroute.utils.version_gating import gate_feature, is_feature_enabled
import click


# Example 1: Gating a command with minimum version requirement
@gate_feature(
    feature_name="GraphQL Support",
    min_version="0.3.0",
    preview_message="GraphQL support will be available in REROUTE v0.3.0 or later."
)
@click.command()
def setup_graphql():
    """Setup GraphQL endpoint (v0.3.0+)."""
    click.echo("Setting up GraphQL...")


# Example 2: Gating with specific version range
@gate_feature(
    feature_name="Legacy API",
    min_version="0.2.0",
    max_version="0.2.9",
    preview_message="Legacy API is only available in v0.2.x releases."
)
@click.command()
def create_legacy_api():
    """Create legacy API endpoints (v0.2.0 - v0.2.9)."""
    click.echo("Creating legacy API...")


# Example 3: Gating for experimental features
@gate_feature(
    feature_name="Experimental Feature",
    enabled_versions=["0.2.1", "0.2.2"],  # Only available in specific versions
    preview_message="This experimental feature is only available in specific versions."
)
@click.command()
def experimental_feature():
    """Experimental feature (v0.2.1, v0.2.2 only)."""
    click.echo("Running experimental feature...")


# Example 4: Checking feature status programmatically
def check_feature_availability():
    """Check if features are available in current version."""

    from reroute import __version__

    # Using the built-in feature gates
    print(f"REROUTE Version: {__version__}")
    print(f"Database init available: {is_feature_enabled('database_init')}")
    print(f"Auth scaffolding available: {is_feature_enabled('auth_scaffolding')}")
    print(f"GraphQL support available: {is_feature_enabled('graphql_support')}")


# Example 5: Creating custom version gates
from reroute.utils.version_gating import is_version_enabled

def custom_feature_gate():
    """Custom feature gating logic."""

    from reroute import __version__

    # Check if current version meets requirements
    if is_version_enabled(__version__, min_version="0.2.0"):
        print("Feature available: v0.2.0+ detected")
        # Implement feature
    else:
        print("Feature not available: requires v0.2.0+")
        # Show preview or error


if __name__ == "__main__":
    # Example usage
    check_feature_availability()
    custom_feature_gate()