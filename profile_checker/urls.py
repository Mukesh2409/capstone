from django.urls import path
from . import views

app_name = 'profile_checker'

urlpatterns = [
    path('', views.index, name='index'),
    path('wholeinsta_fetch/', views.wholeinsta_fetch, name='wholeinsta_fetch'),
]
