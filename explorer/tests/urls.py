from django.urls import include, re_path
from django.contrib import admin
from explorer.urls import urlpatterns

admin.autodiscover()

urlpatterns += [re_path(r"^admin/", include(admin.site.urls))]
