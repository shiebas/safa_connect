import json
from django import template
from django.utils.safestring import mark_safe
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
def pprint(value):
    """
    Pretty print a JSON object or Python dictionary
    
    Usage:
        {{ my_dict|pprint }}
    """
    try:
        if isinstance(value, str):
            # Try to parse the string as JSON
            value = json.loads(value)
        
        # Convert to a formatted JSON string
        formatted_json = json.dumps(value, indent=2, sort_keys=True)
        
        # Return the formatted JSON as a safe string
        return mark_safe(formatted_json)
    except Exception as e:
        return f"Error formatting JSON: {str(e)}"

@register.filter
@stringfilter
def highlight_json(value):
    """
    Syntax highlight a JSON string
    
    Usage:
        {{ json_string|highlight_json }}
    """
    try:
        # Parse the JSON string
        parsed = json.loads(value)
        
        # Convert back to a formatted JSON string
        formatted = json.dumps(parsed, indent=2, sort_keys=True)
        
        # Apply syntax highlighting
        highlighted = formatted.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Highlight different parts of the JSON
        highlighted = highlighted.replace(
            r'"([^"]+)":', r'<span class="json-key">&quot;\1&quot;:</span>'
        )
        highlighted = highlighted.replace(
            r': "([^"]+)"', r': <span class="json-string">&quot;\1&quot;</span>'
        )
        highlighted = highlighted.replace(
            r': ([0-9]+)', r': <span class="json-number">\1</span>'
        )
        highlighted = highlighted.replace(
            r': (true|false)', r': <span class="json-boolean">\1</span>'
        )
        highlighted = highlighted.replace(
            r': null', r': <span class="json-null">null</span>'
        )
        
        # Wrap in a pre tag for formatting
        return mark_safe(f'<pre class="json-highlight">{highlighted}</pre>')
    except Exception as e:
        return f"Error highlighting JSON: {str(e)}"