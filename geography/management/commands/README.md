# Model Field Management Commands

This directory contains management commands for automating common tasks related to model fields.

## add_model_field

This command automates the process of adding a field to a model and updating all the necessary files.

### Usage

```bash
python manage.py add_model_field <model> <field_name> <field_type> [options]
```

### Arguments

- `model`: The name of the model to add the field to (e.g., Club)
- `field_name`: The name of the field to add (e.g., description)
- `field_type`: The type of the field to add (e.g., CharField, IntegerField)

### Options

- `--max_length`: Max length for CharField
- `--null`: Set field as nullable
- `--blank`: Set field as blank
- `--default`: Default value for the field
- `--choices`: Choices for the field (e.g., GENDER_CHOICES)
- `--verbose_name`: Verbose name for the field
- `--help_text`: Help text for the field
- `--update_list`: Update list template
- `--list_position`: Position in list template (0-based index)
- `--update_detail`: Update detail template
- `--update_form`: Update form template
- `--app_name`: App name (default: geography)

### Examples

Add a description field to the Club model:

```bash
python manage.py add_model_field Club description TextField --blank --update_list --update_detail --update_form
```

Add a status field to the Region model with choices:

```bash
python manage.py add_model_field Region status CharField --max_length 20 --choices STATUS_CHOICES --default ACTIVE --update_list --update_detail --update_form
```

### What it does

1. Adds the field to the model in models.py
2. Adds the field to the form's fields list in forms.py
3. Adds a new column to the list template if --update_list is specified
4. Adds a new section to the detail template if --update_detail is specified
5. Adds a new form field to the form template if --update_form is specified

### After running the command

After running the command, you need to:

1. Run `python manage.py makemigrations` to create the migration file
2. Run `python manage.py migrate` to apply the migration

### Notes

- The command will validate that the model exists and the field doesn't already exist
- The command will try to find the best place to insert the field in the model
- The command will try to find the best place to insert the field in the templates
- If any of the files can't be found or the patterns don't match, the command will show a warning but continue with the other files