from django.urls import path
from . import views

app_name = 'emails'

urlpatterns = [
    path('', views.index, name='index'), 
    path('track/open/<uuid:tracking_id>/pixel.png', views.track_email_open, name='track_open'),
    path('track/click/<uuid:tracking_id>/', views.track_link_click, name='track_click'),
]
