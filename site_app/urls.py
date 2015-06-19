from django.conf.urls import url 

from . import views

urlpatterns = [ 
    url(r'^InsiderTransactions/(.*)$', views.insider_transactions_ticker, name='insider_transactions_ticker'),
    url(r'^InsiderTransactions$', views.insider_transactions_main, name='insider_transactions_main'),
    url(r'^search_redirect/$', views.search_redirect, name='search_redirect'),
    url(r'^$', views.insider_transactions_main, name='index'),
]
