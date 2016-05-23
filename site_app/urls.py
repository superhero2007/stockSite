from django.conf.urls import url 

from . import views

urlpatterns = [ 
    url(r'^Ticker/(.*)$', views.ticker, name='ticker'),
    url(r'^Ticker/', views.ticker,name='tickerbase'),
    url(r'^Signals$', views.signals, name='signals'),
    url(r'^search_redirect/$', views.search_redirect, name='search_redirect'),
    url(r'^(.*)$', views.signals, name='index'),
]
