from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path

from explorer.urls import urlpatterns

admin.autodiscover()

urlpatterns += [
    path('admin/', admin.site.urls),
]

urlpatterns += staticfiles_urlpatterns()
