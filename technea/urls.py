# главный urls.py (проект)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('pdf-viewer/api/', include('pdf_viewer.urlsss')),  # подключаем API endpoints
    path('pdf-viewer/', include('pdf_viewer.urlsss_html')),  # подключаем HTML routes
    path('accounts/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)