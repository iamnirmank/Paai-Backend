from rest_framework import routers
from django.urls import path, include
from . import views

router = routers.DefaultRouter()
router.register(r'document', views.DocumentViewSet, basename='document')
router.register(r'query', views.QueryViewSet, basename='query')
router.register(r'rooms', views.RoomsViewSet, basename='rooms')

urlpatterns = [
    path('api/', include(router.urls)),  
    path('accounts/', include('allauth.urls')),
]