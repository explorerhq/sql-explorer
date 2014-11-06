from django.conf.urls import patterns, url, include
from django.contrib import admin
from explorer.urls import urlpatterns

admin.autodiscover()

urlpatterns += patterns('',
    url(r'^admin/', include(admin.site.urls)),
)