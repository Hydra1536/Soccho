from django.conf import settings
from django.contrib import admin
from django.http import Http404
from django.urls import path


def admin_not_found(_request):
    raise Http404('Not Found')


admin_path = settings.ADMIN_URL_PATH.strip('/') + '/'

urlpatterns = [
    path('admin/', admin_not_found, name='blocked-admin-default'),
    path(admin_path, admin.site.urls),
]
