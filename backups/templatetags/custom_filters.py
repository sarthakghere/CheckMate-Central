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
