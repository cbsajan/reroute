"""
Test script to preview the questionary checkbox styling.
Run this in cmd.exe or PowerShell (not Git Bash).
"""

import questionary
from questionary import Style

# Custom questionary style - uniform colors for all items
custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),               # Question mark
    ('question', 'bold'),                        # Question text
    ('answer', 'fg:#f44336 bold'),               # Final selected answer
    ('pointer', 'fg:#673ab7 bold'),              # Pointer (»)
    ('highlighted', 'fg:#673ab7 bold'),          # Currently highlighted item
    ('selected', ''),                            # Selected/checked items - NO special styling
    ('checkbox-selected', ''),                   # Checkbox for selected items - NO special styling
    ('checkbox', ''),                            # Checkbox for unselected items - NO special styling
    ('separator', 'fg:#cc5454'),                 # Separators
    ('instruction', ''),                         # Instruction text
    ('text', ''),                                # Normal text
    ('disabled', 'fg:#858585 italic')            # Disabled items
])

# Test the checkbox
selected_methods = questionary.checkbox(
    "Select HTTP methods to generate:",
    choices=[
        questionary.Choice("GET", checked=True),
        questionary.Choice("POST", checked=True),
        questionary.Choice("PUT", checked=False),
        questionary.Choice("PATCH", checked=False),
        questionary.Choice("DELETE", checked=False),
    ],
    style=custom_style
).ask()

print(f"\nYou selected: {', '.join(selected_methods)}")
