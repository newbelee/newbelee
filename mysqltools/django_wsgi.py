import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'mycitsm.settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
