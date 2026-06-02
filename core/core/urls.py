"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

def home(request):
    """Redirige vers la première table disponible ou vers l'admin"""
    from menu.models import Table
    table = Table.objects.filter(is_active=True).first()
    if table:
        return redirect('menu:menu', table_uuid=table.uuid)
    return redirect('admin:index')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('m/', include('menu.urls', namespace='menu')),
    path('staff/', include('menu.urls_staff', namespace='staff')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
