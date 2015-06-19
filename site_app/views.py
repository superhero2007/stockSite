from django.contrib.auth.decorators import login_required

from pymongo import MongoClient
from django.core.urlresolvers import reverse
from django.shortcuts import render,redirect
import sys
import pandas as pd
from django.conf import settings
import imp
import os
import datetime

mongo = imp.load_source('*', os.path.join(settings.STATIC_ROOT,'AccessMongo.py'))
sql = imp.load_source('*', os.path.join(settings.STATIC_ROOT,'Access_SQL_Database.py'))


# Create your views here.
from django.http import HttpResponse
from django.template import RequestContext, loader


@login_required
def search_redirect(request):
    if request.method == 'GET':
        ticker = request.GET.get('ticker','')        
        return redirect(reverse('insider_transactions_ticker',args={ticker}))

@login_required
def insider_transactions_main(request):
    ## Load insider transactions data
    mongo_conn = mongo.AccessMongo()
    a,b,processed_forms_with_features = mongo_conn.connect_transactions_db()

    signal_data = pd.DataFrame(list(processed_forms_with_features.find({'SignalGenerated':True,
                                                                        'SignalConfidence':{'$gte':0.6},
                                                                        'MarketCap':{'$gte':300000000}})))

    signal_data['AcceptedDate'] = pd.to_datetime(signal_data['AcceptedDate'])
    signal_data['SignalGenerationDate'] = signal_data.SignalGenerationDate.apply(lambda x: pd.to_datetime(x))

    signal_data.sort('SignalGenerationDate', ascending=False, inplace=True)

    signal_data_columns = ['Ticker','MarketCap','CompanyName','zacks_x_sector_desc','zacks_x_ind_desc','URL','AcceptedDate','FilerName',
                           'InsiderTitle','Director','TransType',
                           'DollarValue','SignalDirection','SignalConfidence','SignalGenerationDate']


    signal_data = signal_data[signal_data_columns]

    signal_data = signal_data.to_dict(orient='records')

    template = loader.get_template('site_app/insider_transactions_main.html')

    context = RequestContext(request,{'signal_data':signal_data})

    return HttpResponse(template.render(context))

@login_required
def insider_transactions_ticker(request,ticker):
    ticker = ticker.upper()
    ## Load insider transactions data
    mongo_conn = mongo.AccessMongo()
    a,b,processed_forms_with_features = mongo_conn.connect_transactions_db()

    ticker_data = pd.DataFrame(list(processed_forms_with_features.find({'Ticker':ticker})))
    if (not(len(ticker_data))):
        template = loader.get_template('site_app/ticker_not_found.html')
        context = RequestContext(request,{'ticker':ticker})
        return HttpResponse(template.render(context))


    ticker_data.sort('AcceptedDate', ascending=False, inplace=True)

    ticker_data_columns = ['CompanyName','zacks_x_sector_desc','zacks_x_ind_desc','URL','AcceptedDate','FilerName','InsiderTitle','Director','TenPercentOwner','TransType',
                           'DollarValue','SignalDirection','SignalConfidence','SignalGenerationDate',
                           'F_EOD_1q_abs_return','F_EOD_2q_abs_return']

    ticker_data = ticker_data[ticker_data_columns]
    ticker_data['AcceptedDate'] = pd.to_datetime(ticker_data['AcceptedDate'])
    ticker_data['SignalGenerationDate'] = pd.to_datetime(ticker_data['SignalGenerationDate'])

    ## Load price data
    sql_conn = sql.Access_SQL_Data()

    price_db_columns = ['price_date','close','adj_close', 'adj_vol',
                        'market_cap','VolSMA30','high_52wk','low_52wk']

    price_db = sql_conn.get_qm_eod_data(ticker=ticker,start_date=datetime.datetime(2002,1,1),data_list=price_db_columns)
    price_db['Index'] = range(0,len(price_db))
    price_db['Date'] = price_db.index
    price_db.set_index(['Index'],inplace=True)

    if (not(len(price_db))):
        template = loader.get_template('site_app/ticker_not_found.html')
        context = RequestContext(request,{'ticker':ticker})
        return HttpResponse(template.render(context))

    #convert to JSON for exchange with JS
    chart_data = price_db.to_json(orient='records', date_format='iso') 
    table_data = ticker_data.to_json(orient='records', date_format='iso')

    # # Do some formatting on the ticker data
    # ticker_data.sort(['Date1','Text4'],ascending=[True, True],inplace=True)

    #find cooresponding graph and table datapoints
    #it's a bit convoluted, but it'll make the JS graphing function much simpler
    #   grab the index in price_db (graph) that cooresponds to the entry in ticker_data (table)
    #     make sure your db pulls these values out as datetime objects (last if statement)
    # graph_marker_data = [     {
    #                             "index": g_index, 
    #                             # "value": price_db['Adj Close'][g_index],
    #                             "tableIndex": t_index,
    #                             # "tableDateTime": t_date.value, #just for sorting the table
    #                             "Percent1": ticker_data['Percent1'][t_index], 
    #                             "Text4": ticker_data['Text4'][t_index]
    #                           } 
    #                             for t_index, t_date in  enumerate(ticker_data['Date1'])
    #                                 for g_index, g_val in enumerate(price_db['Date'])
    #                                     if g_val.date() == t_date.date()
    #                         ] 

    #data for markers
    #   index: index of date on graph (x axis)
    #   value: stock price (y axis)
    #   Percent1: value to threshold
    #   Text4: LONG or SHORT
    # graph_marker_data = { 
    #                         count: { 
    #                             "index": tuple_data[0], 
    #                             "value": price_db['Adj Close'][tuple_data[0]], 
    #                             "Percent1": tuple_data[1],
    #                             "Text4": tuple_data[2]
    #                         } 
    #                             for count, tuple_data in enumerate(graph_marker_indicies) 
    #                     }
    # ticker_data.Date1 = ticker_data.Date1.apply(lambda x: x.strftime("%m/%d/%Y %I:%M%p"))
    # ticker_data.Date2 = ticker_data.Date2.apply(lambda x: None if pd.isnull(x) else x.strftime("%m/%d/%Y %I:%M%p"))

    it_data = ticker_data.to_dict(orient='records')
    graph_marker_data = [     {
                                "index": g_index, 
                                # "value": price_db['Adj Close'][g_index],
                                "tableIndex": t_index,
                                # "tableDateTime": t_date.value, #just for sorting the table
                                "SignalConfidence": it_data[t_index]['SignalConfidence'], 
                                "1qReturn": it_data[t_index]['F_EOD_1q_abs_return'], 
                                "2qReturn": it_data[t_index]['F_EOD_2q_abs_return'], 
                                "FilerName": it_data[t_index]['FilerName'],
                                "SignalDirection": it_data[t_index]['SignalDirection']
                              } 
                                for t_index, t_val in  enumerate(it_data)
                                    for g_index, g_val in enumerate(price_db['Date'])
                                        if ((g_val.date() == t_val['AcceptedDate'].date()) & pd.notnull(t_val['SignalConfidence']))
                            ] 
    template = loader.get_template('site_app/insider_transactions_ticker.html')
    l = price_db.index[-1]
    context = RequestContext(request,{'ticker':ticker,
                                      'CompanyName':ticker_data.loc[0,'CompanyName'],
                                      'zacks_sector':ticker_data.loc[0,'zacks_x_sector_desc'],
                                      'zacks_ind':ticker_data.loc[0,'zacks_x_ind_desc'],
                                      'price_db_latest_date':price_db.loc[l,'Date'].date(),
                                       'latest_bar':price_db.iloc[-1].to_dict(),
                                       'avg_trading_vol':price_db.loc[l,'close']*price_db.loc[l,'VolSMA30'],
                                      'chart_data':chart_data,
                                      'table_data':table_data,
                                      'graph_marker_data':graph_marker_data,
                                      'it_data':it_data,
                                      'price_db':price_db}) # may have to convert price db to dict
    return HttpResponse(template.render(context))


##### note: this is a slightly less verbose way of writing the above code:
#####           it replaces RequestContext and HttpResponse with a dict and render()
    # context = {'ticker':ticker,
    #           'company_name':ticker_data.ix[0,'bb_name'],
    #           'zacks_sector':ticker_data.ix[0,'zacks_x_sector_desc'],
    #           'zacks_industry':ticker_data.ix[0,'zacks_x_ind_desc'],
    #           'price_db_latest_date':price_db.index[-1],
    #           'latest_bar':price_db.ix[-1].to_dict(),
    #           'avg_trading_vol':price_db.ix[-1,'close']*price_db.ix[-1,'VolSMA30'],
    #           'chart_data':chart_data,
    #           'it_data':it_data,
    #           'price_db':price_db} # may have to convert price db to dict
    # return render(request, 'site_app/strategy1_ticker.html', context)

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

