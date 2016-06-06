from django.contrib.auth.decorators import login_required

from django.core.urlresolvers import reverse
from django.shortcuts import render,redirect
from django.conf import settings

from sqlalchemy import create_engine,select,Table, Column, MetaData,sql

import sys
import pandas as pd
import imp
import os
import datetime

#mongo = imp.load_source('*', os.path.join(settings.STATIC_ROOT,'AccessMongo.py'))
#sql = imp.load_source('*', os.path.join(settings.STATIC_ROOT,'Access_SQL_Database.py'))


# Create your views here.
from django.http import HttpResponse
from django.template import RequestContext, loader


@login_required
def search_redirect(request):
    if request.method == 'GET':
        ticker = request.GET.get('ticker','')        
        return redirect(reverse('ticker',args={ticker}))

@login_required
def signals(request):
    SQL_ENGINE = create_engine('mysql+mysqldb://root:dodona@dodona/website')
    SQL_CONN = SQL_ENGINE.connect()
    SQL_META = MetaData(bind=SQL_ENGINE)
    signals = Table('signals', SQL_META, autoload=True)

    today = datetime.datetime.now() 
    query = sql.select([signals]).where((signals.c.Date >= today-datetime.timedelta(days=7)) & (signals.c.Date <= today))

    signal_data = pd.read_sql_query(query, SQL_CONN, index_col=None, parse_dates=['Date']).sort_index()
    signal_data = signal_data[signal_data.SS_SignalDirection.isin(['Long','Short'])]

    signal_data = signal_data[(signal_data.close >=5) & (signal_data.market_cap >=300000000) & (signal_data.market_cap <=30000000000)]

    #signal_data['SS_SignalGenerationDate'] = signal_data['SS_SignalGenerationDate'].apply(lambda x: pd.to_datetime(x,errors = 'coerce'))
    #signal_data.sort_values('SS_SignalGenerationDate', ascending=False, inplace=True)
    signal_data.sort_values('Date', ascending=False, inplace=True)

    signal_data_columns = ['Date','bb_ticker','market_cap','zacks_x_sector_desc','zacks_m_ind_desc','SS_SignalDirection']

    signal_data = signal_data[signal_data_columns]

    signal_data = signal_data.to_dict(orient='records')

    context = {'signal_data':signal_data}
    SQL_CONN.close()
    SQL_ENGINE.dispose()

    return render(request, 'site_app/signals.html', context)

@login_required
def ticker(request,ticker):
    ticker = ticker.upper()
    st_df_columns = ['Date','market_cap','name','volume','zacks_x_sector_desc','zacks_m_ind_desc','close','adj_close','SS_SignalDirection','SS_SignalConfidence_XGB']

    SQL_ENGINE = create_engine('mysql+mysqldb://root:dodona@dodona/website')
    SQL_CONN = SQL_ENGINE.connect()

    query = "select * from signals where bb_ticker='%s'"%ticker
    st_df = pd.read_sql_query(query, SQL_CONN, index_col=None, parse_dates=['Date']).sort_index()

    ## Check if stacked signal data exists
    if (not(len(st_df))):
        template = loader.get_template('site_app/ticker_not_found.html')
        context = RequestContext(request,{'ticker':ticker})
        return HttpResponse(template.render(context))

    st_df.zacks_m_ind_desc = st_df.zacks_m_ind_desc.astype(str).map(lambda x: x.title())

    ## add some info to st_df
    st_df['volume_sma30'] = pd.rolling_mean(st_df.volume,30)
    st_df['daily_average_trading_value'] = st_df['volume_sma30'] * st_df.close

    ## sort and reset index 
    st_df.sort_values('Date', ascending=True, inplace=True)
    st_df.set_index('Date',inplace = True) 

    ## latest signal 
    st_df_f = st_df[st_df.SS_SignalDirection.notnull()]
    latest_signal = st_df_f.SS_SignalDirection.iloc[-1]
    latest_signal_date = st_df_f.index[-1].strftime('%m/%d/%Y')

    st_df['Date'] = st_df.index
    st_df.reset_index(inplace = True,drop=True)

    #convert to JSON for exchange with JS
    chart_data = st_df.to_json(orient='records', date_format='iso') 

    
    context = {'ticker':ticker,
               'latest_bar':st_df.iloc[-1].to_dict(),
               'chart_data':chart_data,
               'latest_signal':latest_signal,
               'latest_signal_date':latest_signal_date}

    SQL_CONN.close()
    SQL_ENGINE.dispose()

    return render(request, 'site_app/ticker.html', context)

# def ticker(request,ticker):
#     ticker = ticker.upper()

#     st_df_columns = ['Date','market_cap','volume','zacks_x_sector_desc','zacks_x_ind_desc','close','adj_close','SS_SignalDirection','SS_SignalConfidence_RF','SS_SignalConfidence_XGB',
#                      'IT_1q_NPR','IT_Long_180_IT_SignalConfidence_RF','IT_Short_180_IT_SignalConfidence_GB','MIQ_smart_sentiment_7d','MIQ_smart_sentiment_30d',
#                      'SI_ActiveInventory_ActiveUtilisationByQuantity_x','SI_MarketColour_PcFreeFloatQuantityOnLoan','SI_MarketColour_DaysToCover',
#                      'rating_mean','tp_mean_est']
    
#     it_df_columns = ['URL','AcceptedDate','FilerName','InsiderTitle','Director','TenPercentOwner','TransType',
#                             'DollarValue','IT_SignalDirection','IT_SignalConfidence_RF','IT_SignalGenerationDate']

#     mongo_conn = MongoClient('localhost',replicaset = 'mongo_repl0',readPreference='secondaryPreferred')
#     stsig = mongo_conn.signal_stacker_db.stacked_signals
#     pfwf = mongo_conn.transactions_db.processed_forms_with_features

#     ## Load ticker data
#     st_df = pd.DataFrame(list(stsig.find({'bb_ticker':ticker},{c:1 for c in st_df_columns})))

#     it_df = pd.DataFrame(list(pfwf.find({'bb_ticker':ticker,'AddFeaturesStatus':'ADDED'},{c: 1 for c in it_df_columns})))


#     ## Check if stacked signal data exists
#     if (not(len(st_df))):
#         template = loader.get_template('site_app/ticker_not_found.html')
#         context = RequestContext(request,{'ticker':ticker})
#         return HttpResponse(template.render(context))

#     ## add some info to st_df
#     st_df.drop('_id',axis=1,inplace=True) ### need to do this else to_json gives an error
#     st_df['volume_sma30'] = pd.rolling_mean(st_df.volume,30)
#     st_df['daily_average_trading_value'] = st_df['volume_sma30'] * st_df.close

#     ## sort and reset index 
#     st_df.sort_values('Date', ascending=True, inplace=True)
#     st_df.set_index('Date',inplace = True) 
#     if (len(it_df)):
#         it_df.sort_values('AcceptedDate', ascending=False, inplace=True)
#         it_df.reset_index(inplace = True,drop=True)
#         it_df.drop('_id',axis=1,inplace=True) ### need to do this else to_json gives an error

#     # ticker_data = ticker_data[ticker_data_columns]
#     # ticker_data['AcceptedDate'] = pd.to_datetime(ticker_data['AcceptedDate'])
#     # ticker_data['SignalGenerationDate'] = ticker_data.SignalGenerationDate.apply(lambda x: pd.to_datetime(x))

#     # build marker data
#     graph_marker_data = []
#     for t_index, t_val in it_df.iterrows():
#         if pd.notnull(t_val['IT_SignalConfidence_RF']):
#             g_index = st_df.index.searchsorted(t_val.AcceptedDate.date())
#             if g_index < len(st_df):
#                 graph_marker_data.append({
#                     "index": g_index, 
#                     "tableIndex": t_index,
#                     "IT_SignalConfidence_RF": t_val['IT_SignalConfidence_RF'], 
#                     "FilerName": t_val['FilerName'],
#                     "IT_SignalDirection": t_val['IT_SignalDirection']})

#     st_df['Date'] = st_df.index
#     st_df.reset_index(inplace = True,drop=True)

#     #convert to JSON for exchange with JS
#     chart_data = st_df.to_json(orient='records', date_format='iso') 
#     table_data = it_df.to_json(orient='records', date_format='iso')

#     #convert it_df to dictionary for display as table
#     it_df = it_df.to_dict(orient='records')

#     context = {'ticker':ticker,
#                'latest_bar':st_df.iloc[-1].to_dict(),
#                'chart_data':chart_data,
#                'table_data':table_data,
#                'it_data':it_df,
#                'graph_marker_data':graph_marker_data}

#     return render(request, 'site_app/ticker.html', context)


@login_required
def ticker_not_found(request):
    template = loader.get_template('site_app/ticker_not_found.html')
    context = RequestContext(request)

    return HttpResponse(template.render(context))


@login_required
def macro_signals(request):
    SQL_ENGINE = create_engine('mysql+mysqldb://root:dodona@dodona/website')
    SQL_CONN = SQL_ENGINE.connect()
    SQL_META = MetaData(bind=SQL_ENGINE)
    signals = Table('macro_signal', SQL_META, autoload=True)

    signal_data = pd.read_sql_table('macro_signal',SQL_ENGINE)

    signal_data = signal_data[['price_date','sp_close','rf_conf','conf_threshold']]
    signal_data.columns = ['Date','sp_close','rf_conf','conf_threshold']

    latest_signal = 'Long' if signal_data.rf_conf.iloc[-1] >= signal_data.conf_threshold.iloc[-1] else 'Short' if signal_data.rf_conf.iloc[-1] <= 1-signal_data.conf_threshold.iloc[-1] else 'Neutral'
    latest_signal_date = signal_data.Date.iloc[-1].strftime('%m/%d/%Y')

    signal_data = signal_data.to_json(orient='records',date_format='iso')

    context = {'chart_data':signal_data,
               'latest_signal':latest_signal,
               'latest_signal_date':latest_signal_date}

    SQL_CONN.close()
    SQL_ENGINE.dispose()

    return render(request, 'site_app/macro_signals.html', context)


