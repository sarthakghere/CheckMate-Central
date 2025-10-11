import os
from django import template

register = template.Library()

@register.filter
def basename(value):
    """Returns the base name of a file path."""
    return os.path.basename(value)

@register.filter
def get_item(dictionary, key):
    """Returns the value of a dictionary for a given key."""
    return dictionary.get(key)

@register.filter
def format_bytes(size):
    """Converts bytes to a human-readable format."""
    if size is None:
        return "0 Bytes"
    power = 1024
    n = 0
    power_labels = {0: 'Bytes', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size >= power and n < len(power_labels) -1 :
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}"
