"""
Simple Model Template for REROUTE

Generates minimal models with just a 'name' field by default.
Users can edit the file to add more fields as needed.
"""

# Default template - just name field, user can customize later
DEFAULT_TEMPLATE = {
    "description": "Auto-generated model - customize fields as needed",
    "fields": [
        {"name": "name", "type": "String(100)", "nullable": False},
    ],
}


def get_template(model_name: str) -> dict:
    """
    Get template for given model name

    Args:
        model_name: Name of the model (e.g., "User", "Product")

    Returns:
        Template dictionary with minimal fields
    """
    template = DEFAULT_TEMPLATE.copy()

    # Auto-generate table name from model name
    # Convert CamelCase to snake_case plural
    import re
    snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', model_name).lower()
    table_name = f"{snake_case}s" if not snake_case.endswith('s') else snake_case

    template["table_name"] = table_name
    template["model_name"] = model_name

    return template
