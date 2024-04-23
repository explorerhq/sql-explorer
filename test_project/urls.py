from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include

# Installing to /explorer/ better mimics likely production setups
# Explorer is probably *not* running at the Django project root
urlpatterns = [
    path("explorer/", include("explorer.urls"))
]

admin.autodiscover()

urlpatterns += [
    path("admin/", admin.site.urls),
]

urlpatterns += staticfiles_urlpatterns()
