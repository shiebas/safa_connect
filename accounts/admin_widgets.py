from django.forms.widgets import TextInput
from django.utils.html import format_html
from django.urls import reverse

class SafaIDWidget(TextInput):
    """Custom widget for SAFA ID field with generation button"""
    template_name = 'admin/widgets/safa_id_widget.html'
    
    class Media:
        js = ('js/safa_id_generator.js',)
    
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['generate_url'] = reverse('admin:generate_safa_id_ajax')
        return context
