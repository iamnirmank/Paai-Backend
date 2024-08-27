from rest_framework import routers
from django.urls import path, include
from . import views

router = routers.DefaultRouter()
router.register(r'document', views.DocumentViewSet)
router.register(r'query', views.QueryViewSet)
router.register(r'combinedchunk', views.CombinedChunkViewSet)
router.register(r'rooms', views.RoomsViewSet)

urlpatterns = [
    path('api/', include(router.urls)),  
    path('accounts/', include('allauth.urls')),
]