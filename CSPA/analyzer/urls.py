from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.show_site, name='show_site'),
    url(r'^query', views.find_games, name='find_games'),
]
