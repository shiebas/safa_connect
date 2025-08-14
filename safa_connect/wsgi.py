import os
# Add the patch import at the top
try:
    import patches  # noqa
except ImportError:
    pass

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safa_connect.settings')

application = get_wsgi_application()
