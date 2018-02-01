from django.conf.urls import url 

from . import views

urlpatterns = [ 
    url(r'^EquitySignals/Ticker/(.*)$', views.equities_ticker, name='equities_ticker'),
    url(r'^EquitySignals/Ticker/', views.equities_latest_signals,name='tickerbase'),
    url(r'^EquitySignals/LatestSignals$', views.equities_latest_signals, name='equities_latest_signals'),
    url(r'^EquitySignals/SectorIndustry$', views.equities_sector_industry_signals, name='equities_sector_industry_signals'),

    url(r'^InsiderTransactions/LatestFilings$', views.insider_transactions_latest_filings, name='insider_transactions_latest_filings'),
    url(r'^InsiderTransactions/Ticker/(.*)$', views.insider_transactions_ticker, name='insider_transactions_ticker'),
    url(r'^MacroSignals$', views.macro_signals, name='macro_signals'),
    url(r'^under_development$', views.under_development, name='under_development'),
    url(r'^search_redirect/$', views.search_redirect, name='search_redirect'),
    url(r'^(.*)$', views.equities_latest_signals, name='index'),
]
