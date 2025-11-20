"""
Test script to simulate update notification
"""

import click
from reroute.cli.update_checker import parse_version, save_check_time, get_cache_file

def simulate_update_notification():
    """Simulate what happens when update is available."""

    current_version = "0.0.1"  # Your test version
    latest_version = "0.1.1"   # Simulated PyPI version

    # Compare versions
    current = parse_version(current_version)
    latest = parse_version(latest_version)

    print(f"\nCurrent version: {current_version}")
    print(f"Latest version (simulated): {latest_version}")
    print(f"Update available: {latest > current}\n")

    if latest > current:
        # Display update notification (same as in update_checker.py)
        click.echo()
        click.secho("=" * 60, fg='yellow')
        click.secho(f"  Update available: {current_version} -> {latest_version}", fg='yellow', bold=True)
        click.secho(f"  Run: pip install --upgrade reroute", fg='cyan')
        click.secho("=" * 60, fg='yellow')
        click.echo()

        # Show cache file location
        cache_file = get_cache_file()
        print(f"Cache file location: {cache_file}")

        # Save test data
        save_check_time(latest_version)
        print(f"Saved check time to cache")

if __name__ == "__main__":
    simulate_update_notification()
