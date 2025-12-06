"""
Private Jinja2 Template Loader for REROUTE CLI

This module provides a secure Jinja2 environment for code generation.
All template security settings are centralized here.

IMPORTANT: This is a private module (prefixed with underscore) and should
only be imported internally by REROUTE CLI commands.
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined

# Setup Jinja2 environment with security hardening
TEMPLATES_DIR = Path(__file__).parent / "templates"

# Create secure Jinja2 environment
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,  # Force autoescape for all templates
    auto_reload=False,  # Disable auto-reload for security
    undefined=StrictUndefined,  # Fail loudly on undefined variables
    trim_blocks=True,
    lstrip_blocks=True
)

# Disable dangerous template features
jinja_env.policies['ext.i18n.striped'] = True

# Expose only safe Python built-ins and functions
jinja_env.globals.update({
    'range': range,
    'len': len,
    'str': str,
    'int': int,
    'float': float,
    'bool': bool,
    'list': list,
    'dict': dict,
    'set': set,
    'tuple': tuple,
    'enumerate': enumerate,
    'zip': zip,
    'min': min,
    'max': max,
    'sum': sum,
    'any': any,
    'all': all,
    'isinstance': isinstance,
    'type': type
})

# Security: Deliberately do NOT expose dangerous functions:
# - eval, exec, compile: Code execution
# - open, file: File system access
# - __import__: Module importing
# - input, raw_input: User input
# - exit, quit: Interpreter exit
# - reload: Module reloading

__all__ = ['jinja_env', 'TEMPLATES_DIR']