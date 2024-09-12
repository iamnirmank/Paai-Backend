from rest_framework import routers
from django.urls import path, include
from . import views

router = routers.DefaultRouter()
router.register(r'user', views.UserViewSet, basename='user')
router.register(r'feedback', views.FeedbackViewSet, basename='feedback')

urlpatterns = [
    path('api/', include(router.urls)),  
    path('accounts/', include('allauth.urls')),
]