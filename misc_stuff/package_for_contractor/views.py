from pymongo import MongoClient
from django.shortcuts import render
import sys
import pandas as pd
conn = MongoClient() 


# Create your views here.
from django.http import HttpResponse
from django.template import RequestContext, loader


def index(request):
    template = loader.get_template('semanteon_dashboard.html')
    context = RequestContext(request)

    return HttpResponse(template.render(context))


def strategy1_dashboard(request):
    template = loader.get_template('site_app/strategy1_dashboard.html')
    context = RequestContext(request)

    return HttpResponse(template.render(context))


def strategy1_ticker(request,ticker):
    ticker_data = ## Load data from mongo ## You can read this in from the file called 'ticker_data.csv' for now

    if (not(len(ticker_data))):
        ### go to ticker not found page

    price_db = ## Load price data from sql ## You can read this from the file called stock_price.csv

    if (not(len(price_db))):
        #### go to ticker not found page

    # Do some formatting on the ticker data
    ticker_data.sort('Date1',ascending=False,inplace=True)
    ticker_data.Date1 = ticker_data.Date1.apply(lambda x: x.strftime("%m/%d/%Y %I:%M%p"))
    ticker_data.Date2 = ticker_data.Date2.apply(lambda x: None if pd.isnull(x) else x.strftime("%m/%d/%Y %I:%M%p"))

    template = loader.get_template('site_app/strategy1_ticker.html')
    it_data = ticker_data.to_dict(orient='records')
    context = RequestContext(request,{'ticker':ticker,
                                      'company_name':ticker_data.ix[0,'bb_name'],
                                      'zacks_sector':ticker_data.ix[0,'zacks_x_sector_desc'],
                                      'zacks_industry':ticker_data.ix[0,'zacks_x_ind_desc'],
                                      'price_db_latest_date':price_db.index[-1],
                                      'latest_bar':price_db.ix[-1].to_dict(),
                                      'avg_trading_vol':price_db.ix[-1,'close']*price_db.ix[-1,'VolSMA30'],
                                      'it_data':it_data,
                                      'price_dd':price_db} # may have to convert price db to dict
    return HttpResponse(template.render(context))

def ticker_not_found(request):
    template = loader.get_template('site_app/ticker_not_found.html')
    context = RequestContext(request)

    return HttpResponse(template.render(context))


## do not need to be designed right now
def strategy2_dashboard(request):
    template = loader.get_template('site_app/strategy2_dashboard.html')
    context = RequestContext(request)

    return HttpResponse(template.render(context))

def strategy2_ticker(request):
    template = loader.get_template('site_app/strategy2_ticker.html')
    context = RequestContext(request)

    return HttpResponse(template.render(context))
