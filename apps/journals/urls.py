from django.urls import path
from . import views

app_name = 'journals'

urlpatterns = [
    path('compose/', views.compose, name='compose'),
]
