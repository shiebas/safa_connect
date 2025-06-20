from django.db import migrations

def make_position_titles_unique(apps, schema_editor):
    """
    Make position titles unique by appending the level if needed
    """
    Position = apps.get_model('accounts', 'Position')
    
    # Group by title to find duplicates
    titles = {}
    for position in Position.objects.all():
        if position.title not in titles:
            titles[position.title] = []
        titles[position.title].append(position)
    
    # Update duplicate titles
    for title, positions in titles.items():
        if len(positions) > 1:
            # First position keeps the original title
            for i, position in enumerate(positions[1:], 1):
                position.title = f"{position.title} ({position.levels})"
                position.save()

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(make_position_titles_unique),
    ]
