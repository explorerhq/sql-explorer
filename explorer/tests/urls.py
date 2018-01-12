from django.conf.urls import *
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from explorer.urls import urlpatterns

admin.autodiscover()

urlpatterns += [
    url(r'^admin/', include(admin.site.get_urls(), 'admin')),
]

urlpatterns += staticfiles_urlpatterns()
