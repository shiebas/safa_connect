from django import template

register = template.Library()

@register.filter(name='points_display')
def points_display(points):
    """Format points for display with suffix"""
    try:
        points = int(points)
        if points == 1:
            return f"{points} pt"
        return f"{points} pts"
    except (ValueError, TypeError):
        return "0 pts"

@register.filter(name='position_suffix')
def position_suffix(position):
    """Add appropriate suffix to position numbers"""
    try:
        position = int(position)
        if position % 10 == 1 and position != 11:
            return f"{position}st"
        elif position % 10 == 2 and position != 12:
            return f"{position}nd"
        elif position % 10 == 3 and position != 13:
            return f"{position}rd"
        else:
            return f"{position}th"
    except (ValueError, TypeError):
        return str(position)

@register.filter(name='goal_difference')
def goal_difference(goals_for, goals_against):
    """Calculate goal difference with proper sign"""
    try:
        diff = int(goals_for) - int(goals_against)
        if diff > 0:
            return f"+{diff}"
        return str(diff)
    except (ValueError, TypeError):
        return "0"
