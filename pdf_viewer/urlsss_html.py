from django.urls import path
from .views import pdf_viewer_interface

urlpatterns = [
    path('', pdf_viewer_interface, name='pdf-viewer'),
]