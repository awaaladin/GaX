"""
URL configuration for banking project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from PIL import Image
from io import BytesIO
from accounts import views as account_views  # Import the dashboard view


@require_http_methods(["GET"])
def placeholder_image(request, width, height):
    """Generate placeholder images dynamically"""
    try:
        width = int(width)
        height = int(height)
        
        # Create a simple placeholder image
        img = Image.new('RGB', (width, height), color='#cccccc')
        
        # Save to BytesIO
        img_io = BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        
        return HttpResponse(img_io.getvalue(), content_type='image/png')
    except:
        # Return a minimal 1x1 pixel image if anything fails
        return HttpResponse(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82',
            content_type='image/png'
        )


urlpatterns = [
    path('admin/', admin.site.urls),

    # Dashboard views
    path('', account_views.dashboard, name='home'),  # Root URL
    path('dashboard/', account_views.dashboard, name='dashboard'),

    # Accounts app URLs
    path('accounts/', include('accounts.urls')),
    path('api/', include('accounts.api_urls')),  # <<-- New API path

    # Placeholder image API
    re_path(r'^api/placeholder/(?P<width>\d+)/(?P<height>\d+)/?$', placeholder_image, name='placeholder_image'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    