from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PDFDocumentViewSet, CommentViewSet, pdf_viewer_interface
from django.views.decorators.csrf import csrf_exempt

router = DefaultRouter()
router.register(r'pdfs', PDFDocumentViewSet, basename='pdf')
router.register(r'comments', CommentViewSet, basename='comment')

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
    
    # DRF auth endpoints
    # path('api-auth/', include('rest_framework.urls')),
]