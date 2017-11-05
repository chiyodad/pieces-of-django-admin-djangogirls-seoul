
from django.conf.urls import url
from django.contrib import admin
from django.conf import settings
from django.contrib.staticfiles.urls import static

urlpatterns = [
    url(r'^admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
