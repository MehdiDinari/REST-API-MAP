"""
URL configuration for route_finder project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.http import JsonResponse

def home(request):
    """Route racine pour vérifier que l'API fonctionne"""
    return JsonResponse({
        "message": "Route Finder API is running",
        "status": "success",
        "version": "1.0",
        "endpoints": {
            "admin": "/admin/",
            "api": "/api/",
        }
    })

def health_check(request):
    """Health check endpoint for monitoring"""
    return JsonResponse({
        "status": "healthy",
        "service": "route-finder-api"
    })

urlpatterns = [
    path('', home, name='home'),  # Route racine - corrige l'erreur 404
    path('health/', health_check, name='health_check'),  # Health check
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]