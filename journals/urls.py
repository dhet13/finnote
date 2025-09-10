from django.urls import path
from . import views

app_name = 'journals'

urlpatterns = [
    path('compose/', views.compose, name='compose'),
    path('my-list/', views.my_journal_list, name='my_list'),
]
