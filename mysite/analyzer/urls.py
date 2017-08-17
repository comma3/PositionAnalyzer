from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.dbquery, name='dbquery'),
    url(r'^query', views.find_games, name='find_games'),
]
