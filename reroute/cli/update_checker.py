"""
REROUTE Update Checker

Checks PyPI for newer versions and notifies users.
"""

import click
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import sys


def get_cache_file() -> Path:
    """Get the path to the update check cache file."""
    # Use user's home directory for cache
    cache_dir = Path.home() / ".reroute"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / "update_check.json"


def should_check_for_updates() -> bool:
    """Check if we should check for updates (once per day)."""
    cache_file = get_cache_file()

    if not cache_file.exists():
        return True

    try:
        with open(cache_file, 'r') as f:
            data = json.load(f)
            last_check = datetime.fromisoformat(data.get('last_check', ''))
            # Check once per day
            return datetime.now() - last_check > timedelta(days=1)
    except (json.JSONDecodeError, ValueError, KeyError):
        return True


def save_check_time(latest_version: Optional[str] = None):
    """Save the last check time and latest version."""
    cache_file = get_cache_file()
    data = {
        'last_check': datetime.now().isoformat(),
        'latest_version': latest_version
    }
    with open(cache_file, 'w') as f:
        json.dump(data, f)


def get_latest_version_from_pypi() -> Optional[str]:
    """Fetch the latest version from PyPI."""
    try:
        import urllib.request
        import urllib.error

        url = "https://pypi.org/pypi/reroute/json"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'reroute-cli')

        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read().decode())
            return data['info']['version']
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, json.JSONDecodeError, TimeoutError):
        # Silently fail - don't interrupt user's work
        return None


def parse_version(version: str) -> tuple:
    """Parse version string to tuple for comparison."""
    try:
        return tuple(int(x) for x in version.split('.'))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def check_for_updates(current_version: str):
    """
    Check for updates and display notification if newer version available.

    This runs asynchronously and doesn't block CLI execution.
    """
    if not should_check_for_updates():
        return

    latest_version = get_latest_version_from_pypi()

    if latest_version:
        save_check_time(latest_version)

        # Compare versions
        current = parse_version(current_version)
        latest = parse_version(latest_version)

        if latest > current:
            # Display update notification
            click.echo()
            click.secho("=" * 60, fg='yellow')
            click.secho(f"  Update available: {current_version} -> {latest_version}", fg='yellow', bold=True)
            click.secho(f"  Run: pip install --upgrade reroute", fg='cyan')
            click.secho("=" * 60, fg='yellow')
            click.echo()
    else:
        # Save check time even if fetch failed
        save_check_time()
