from django.core.management.base import BaseCommand, CommandError
import os
import re
from django.apps import apps
from django.conf import settings

class Command(BaseCommand):
    help = 'Add a field to a model and update related files'

    def add_arguments(self, parser):
        parser.add_argument('model', type=str, help='Model name (e.g., Club)')
        parser.add_argument('field_name', type=str, help='Field name (e.g., description)')
        parser.add_argument('field_type', type=str, help='Field type (e.g., CharField, IntegerField)')
        parser.add_argument('--max_length', type=int, help='Max length for CharField')
        parser.add_argument('--null', action='store_true', help='Set field as nullable')
        parser.add_argument('--blank', action='store_true', help='Set field as blank')
        parser.add_argument('--default', type=str, help='Default value for the field')
        parser.add_argument('--choices', type=str, help='Choices for the field (e.g., GENDER_CHOICES)')
        parser.add_argument('--verbose_name', type=str, help='Verbose name for the field')
        parser.add_argument('--help_text', type=str, help='Help text for the field')
        parser.add_argument('--update_list', action='store_true', help='Update list template')
        parser.add_argument('--list_position', type=int, help='Position in list template (0-based index)')
        parser.add_argument('--update_detail', action='store_true', help='Update detail template')
        parser.add_argument('--update_form', action='store_true', help='Update form template')
        parser.add_argument('--app_name', type=str, default='geography', help='App name (default: geography)')

    def handle(self, *args, **options):
        model_name = options['model']
        field_name = options['field_name']
        field_type = options['field_type']
        app_name = options['app_name']
        
        # Validate model exists
        try:
            model = apps.get_model(app_name, model_name)
        except LookupError:
            raise CommandError(f"Model '{model_name}' not found in app '{app_name}'")
        
        # Check if field already exists
        if hasattr(model, field_name):
            raise CommandError(f"Field '{field_name}' already exists in model '{model_name}'")
        
        # Build field definition
        field_options = []
        if options['max_length']:
            field_options.append(f"max_length={options['max_length']}")
        if options['null']:
            field_options.append("null=True")
        if options['blank']:
            field_options.append("blank=True")
        if options['default'] is not None:
            if field_type == 'CharField' or field_type == 'TextField':
                field_options.append(f"default='{options['default']}'")
            else:
                field_options.append(f"default={options['default']}")
        if options['choices']:
            field_options.append(f"choices={options['choices']}")
        if options['verbose_name']:
            field_options.append(f"verbose_name='{options['verbose_name']}'")
        if options['help_text']:
            field_options.append(f"help_text='{options['help_text']}'")
        
        field_definition = f"{field_name} = models.{field_type}({', '.join(field_options)})"
        
        # Update models.py
        self.update_models_py(app_name, model_name, field_definition)
        self.stdout.write(self.style.SUCCESS(f"Added field '{field_name}' to model '{model_name}' in models.py"))
        
        # Update forms.py
        self.update_forms_py(app_name, model_name, field_name)
        self.stdout.write(self.style.SUCCESS(f"Updated form for model '{model_name}' in forms.py"))
        
        # Update templates if requested
        if options['update_list']:
            self.update_list_template(app_name, model_name, field_name, options['list_position'])
            self.stdout.write(self.style.SUCCESS(f"Updated list template for model '{model_name}'"))
        
        if options['update_detail']:
            self.update_detail_template(app_name, model_name, field_name)
            self.stdout.write(self.style.SUCCESS(f"Updated detail template for model '{model_name}'"))
        
        if options['update_form']:
            self.update_form_template(app_name, model_name, field_name)
            self.stdout.write(self.style.SUCCESS(f"Updated form template for model '{model_name}'"))
        
        self.stdout.write(self.style.SUCCESS(f"Successfully added field '{field_name}' to model '{model_name}'"))
        self.stdout.write(self.style.WARNING("Don't forget to run 'python manage.py makemigrations' and 'python manage.py migrate'"))
    
    def update_models_py(self, app_name, model_name, field_definition):
        """Add the field to the model in models.py"""
        models_path = os.path.join(settings.BASE_DIR, app_name, 'models.py')
        
        with open(models_path, 'r') as file:
            content = file.read()
        
        # Find the model class
        model_pattern = re.compile(f"class {model_name}\\([^)]+\\):(.*?)(?=\\n\\n|$)", re.DOTALL)
        match = model_pattern.search(content)
        
        if not match:
            raise CommandError(f"Could not find model '{model_name}' in {models_path}")
        
        model_content = match.group(1)
        model_end_pos = match.end(1)
        
        # Find a good position to insert the field (after other field definitions)
        lines = model_content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if re.match(r'^\s+\w+ = models\.', line):
                insert_pos = i + 1
        
        # Insert the field definition
        lines.insert(insert_pos, f"    {field_definition}")
        updated_model_content = '\n'.join(lines)
        
        # Replace the old model content with the updated one
        updated_content = content[:match.start(1)] + updated_model_content + content[model_end_pos:]
        
        with open(models_path, 'w') as file:
            file.write(updated_content)
    
    def update_forms_py(self, app_name, model_name, field_name):
        """Add the field to the form's fields list in forms.py"""
        forms_path = os.path.join(settings.BASE_DIR, app_name, 'forms.py')
        
        with open(forms_path, 'r') as file:
            content = file.read()
        
        # Find the form class for the model
        form_pattern = re.compile(f"class {model_name}Form\\(forms\\.ModelForm\\):(.*?)class Meta:(.*?)fields = \\[(.*?)\\]", re.DOTALL)
        match = form_pattern.search(content)
        
        if not match:
            self.stdout.write(self.style.WARNING(f"Could not find form for model '{model_name}' in {forms_path}"))
            return
        
        fields_content = match.group(3)
        fields_end_pos = match.end(3)
        
        # Add the field to the fields list
        if fields_content.strip():
            # Fields list is not empty, add a comma if needed
            if fields_content.strip()[-1] != ',':
                updated_fields = fields_content + f', "{field_name}"'
            else:
                updated_fields = fields_content + f' "{field_name}",'
        else:
            # Fields list is empty
            updated_fields = f'"{field_name}"'
        
        # Replace the old fields list with the updated one
        updated_content = content[:match.start(3)] + updated_fields + content[fields_end_pos:]
        
        with open(forms_path, 'w') as file:
            file.write(updated_content)
    
    def update_list_template(self, app_name, model_name, field_name, position=None):
        """Add a new column to the list template"""
        template_path = os.path.join(settings.BASE_DIR, 'templates', app_name, f"{model_name.lower()}_list.html")
        
        if not os.path.exists(template_path):
            self.stdout.write(self.style.WARNING(f"List template not found at {template_path}"))
            return
        
        with open(template_path, 'r') as file:
            content = file.read()
        
        # Find the table header row
        header_pattern = re.compile(r'<thead>\s*<tr>(.*?)</tr>\s*</thead>', re.DOTALL)
        header_match = header_pattern.search(content)
        
        if not header_match:
            self.stdout.write(self.style.WARNING(f"Could not find table header in {template_path}"))
            return
        
        header_content = header_match.group(1)
        header_end_pos = header_match.end(1)
        
        # Add the new column header
        new_header = f'<th>{field_name.replace("_", " ").title()}</th>'
        
        if position is not None:
            # Insert at specific position
            headers = re.findall(r'<th>.*?</th>', header_content)
            if position >= len(headers):
                position = len(headers)
            headers.insert(position, new_header)
            updated_header = ''.join(headers)
        else:
            # Add at the end (before Actions)
            if 'Actions' in header_content:
                updated_header = header_content.replace('<th>Actions</th>', f'{new_header}\n                <th>Actions</th>')
            else:
                updated_header = header_content + f'\n                {new_header}'
        
        # Replace the old header with the updated one
        updated_content = content[:header_match.start(1)] + updated_header + content[header_end_pos:]
        
        # Find the table row template
        row_pattern = re.compile(r'{%\s*for\s+\w+\s+in\s+\w+\s*%}(.*?){%\s*empty\s*%}', re.DOTALL)
        row_match = row_pattern.search(updated_content)
        
        if not row_match:
            self.stdout.write(self.style.WARNING(f"Could not find row template in {template_path}"))
            with open(template_path, 'w') as file:
                file.write(updated_content)
            return
        
        row_content = row_match.group(1)
        row_end_pos = row_match.end(1)
        
        # Add the new column cell
        model_var = model_name.lower()
        new_cell = f'<td>{{ {{ {model_var}.{field_name}|default:"-" }} }}</td>'
        
        if position is not None:
            # Insert at specific position
            cells = re.findall(r'<td>.*?</td>', row_content)
            if position >= len(cells):
                position = len(cells)
            cells.insert(position, new_cell)
            updated_row = ''.join(cells)
        else:
            # Add at the end (before Actions)
            actions_pattern = re.compile(r'<td>\s*<a.*?btn-danger.*?</td>', re.DOTALL)
            actions_match = actions_pattern.search(row_content)
            
            if actions_match:
                actions_start = actions_match.start()
                updated_row = row_content[:actions_start] + f'{new_cell}\n                ' + row_content[actions_start:]
            else:
                updated_row = row_content + f'\n                {new_cell}'
        
        # Replace the old row with the updated one
        final_content = updated_content[:row_match.start(1)] + updated_row + updated_content[row_end_pos:]
        
        with open(template_path, 'w') as file:
            file.write(final_content)
    
    def update_detail_template(self, app_name, model_name, field_name):
        """Add a new section to the detail template"""
        template_path = os.path.join(settings.BASE_DIR, 'templates', app_name, f"{model_name.lower()}_detail.html")
        
        if not os.path.exists(template_path):
            self.stdout.write(self.style.WARNING(f"Detail template not found at {template_path}"))
            return
        
        with open(template_path, 'r') as file:
            content = file.read()
        
        # Find the card body with model details
        card_body_pattern = re.compile(r'<div class="card-body">(.*?)</div>', re.DOTALL)
        card_body_match = card_body_pattern.search(content)
        
        if not card_body_match:
            self.stdout.write(self.style.WARNING(f"Could not find card body in {template_path}"))
            return
        
        card_body_content = card_body_match.group(1)
        card_body_end_pos = card_body_match.end(1)
        
        # Find the col-md-8 div that contains the details
        col_pattern = re.compile(r'<div class="col-md-8">(.*?)</div>', re.DOTALL)
        col_match = col_pattern.search(card_body_content)
        
        if not col_match:
            self.stdout.write(self.style.WARNING(f"Could not find col-md-8 div in {template_path}"))
            return
        
        col_content = col_match.group(1)
        col_end_pos = col_match.end(1)
        
        # Add the new field display
        model_var = model_name.lower()
        field_display_name = field_name.replace("_", " ").title()
        
        new_field = f'''
                {{% if {model_var}.{field_name} %}}
                <p><strong>{field_display_name}:</strong> {{ {{ {model_var}.{field_name} }} }}</p>
                {{% endif %}}'''
        
        updated_col = col_content + new_field
        
        # Replace the old col content with the updated one
        updated_card_body = card_body_content[:col_match.start(1)] + updated_col + card_body_content[col_end_pos:]
        
        # Replace the old card body with the updated one
        updated_content = content[:card_body_match.start(1)] + updated_card_body + content[card_body_end_pos:]
        
        with open(template_path, 'w') as file:
            file.write(updated_content)
    
    def update_form_template(self, app_name, model_name, field_name):
        """Add a new form field to the form template"""
        template_path = os.path.join(settings.BASE_DIR, 'templates', app_name, f"{model_name.lower()}_form.html")
        
        if not os.path.exists(template_path):
            self.stdout.write(self.style.WARNING(f"Form template not found at {template_path}"))
            return
        
        with open(template_path, 'r') as file:
            content = file.read()
        
        # Find the card body with form fields
        card_body_pattern = re.compile(r'<div class="card-body">(.*?)</div>\s*<div class="card-footer', re.DOTALL)
        card_body_match = card_body_pattern.search(content)
        
        if not card_body_match:
            self.stdout.write(self.style.WARNING(f"Could not find card body in {template_path}"))
            return
        
        card_body_content = card_body_match.group(1)
        card_body_end_pos = card_body_match.end(1)
        
        # Create the new form field
        field_display_name = field_name.replace("_", " ").title()
        
        new_field = f'''
                    <div class="mb-3">
                        <label for="{{{{ form.{field_name}.id_for_label }}}}" class="form-label">{field_display_name}</label>
                        {{% render_field form.{field_name} class="form-control" %}}
                        {{% if form.{field_name}.errors %}}
                        <div class="text-danger small">{{{{ form.{field_name}.errors }}}}</div>
                        {{% endif %}}
                    </div>'''
        
        # Add the new field at the end of the card body
        updated_card_body = card_body_content + new_field
        
        # Replace the old card body with the updated one
        updated_content = content[:card_body_match.start(1)] + updated_card_body + content[card_body_end_pos:]
        
        with open(template_path, 'w') as file:
            file.write(updated_content)