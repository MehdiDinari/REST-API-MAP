from django.urls import path
from .views import SearchLocationView, RouteView, OptimizedRouteView

urlpatterns = [
    path('locations/search/', SearchLocationView.as_view(), name='search-location'),
    path('routes/calculate/', RouteView.as_view(), name='calculate-route'),
    path('routes/optimize/', OptimizedRouteView.as_view(), name='optimize-route'),
]

