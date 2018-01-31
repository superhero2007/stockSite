from django.contrib.auth.decorators import login_required

from django.urls import reverse
from django.shortcuts import render,redirect
from django.conf import settings

import sys,os
import pandas as pd
import datetime,time

from semutils.db_access import Access_SQL_DB, Access_SQL_Source
from sqlalchemy import select,Table, Column

from .forms import SectorForm

# Create your views here.
from django.http import HttpResponse
from django.template import RequestContext, loader

EnterLong = 0.6
EnterShort = 0.4
MySQL_Server = os.environ.get('MySQL_Server')

def wavg(group, avg_name, weight_name):
    """
    In rare instance, we may not have weights, so just return the mean. Customize this if your business case
    should return otherwise.
    """
    d = group[avg_name]
    w = group[weight_name]
    try:
        return (d * w).sum() / w.sum()
    except ZeroDivisionError:
        return d.mean()

@login_required
def search_redirect(request):
    if request.method == 'GET':
        ticker = request.GET.get('ticker','')        
        return redirect(reverse('equities_ticker',args={ticker}))

@login_required
def under_development(request):
    if request.method == 'GET':
        return render(request, 'site_app/under_development.html')

@login_required
def equities_sector_industry_signals(request):
    # connect to sql and tables
    sql_source = Access_SQL_Source(MySQL_Server)
    sql = Access_SQL_DB(MySQL_Server,db='equity_models')
    signals = Table('signals_daily_2017_07_01', sql.META, autoload=True)

    # download data
    today = datetime.datetime.now() 
    signal_data_columns = ['data_date','ticker','market_cap','zacks_x_sector_desc','zacks_m_ind_desc','SignalConfidence']

    if request.method=='POST':
        current_sector_code = request.POST['sectors']
    else:
        current_sector_code = SectorForm().fields['sectors'].choices[0][0]
    
    sector_form = SectorForm(initial={'sectors': current_sector_code})

    query = select([signals.c[x] for x in signal_data_columns]).where(((signals.c.data_date >= today-datetime.timedelta(days=100)) & 
                                                                       (signals.c.data_date <= today)) &
                                                                      (signals.c.zacks_x_sector_code==current_sector_code))

    signal_data = pd.read_sql_query(query, sql.ENGINE, index_col=None, parse_dates=['data_date']).sort_index()
    signal_data.sort_values('data_date',inplace=True)

    # find current sector name
    current_sector_name = signal_data.zacks_x_sector_desc.unique()[0]
                                 
    # filter data for market cap
    #signal_data = signal_data[signal_data.market_cap >=300e6]

    # create consolidated signal for chart
    chart_data = signal_data.groupby('data_date').apply(wavg,'SignalConfidence','market_cap')

    # format signal for javascript
    chart_data.sort_index(inplace=True)
    chart_data = chart_data.to_frame()
    chart_data.reset_index(drop=False,inplace=True)
    chart_data.columns = ['date','signal']
    chart_data['date'] = chart_data['date'].apply(lambda x: time.mktime(x.timetuple()))
    chart_data = chart_data.values.tolist()

    # create table data
    table_data = signal_data.copy()
    table_data['delta_1wk'] = signal_data.groupby('ticker').SignalConfidence.diff(5).round(2)
    table_data['delta_2wk'] = signal_data.groupby('ticker').SignalConfidence.diff(10).round(2)
    table_data['delta_4wk'] = signal_data.groupby('ticker').SignalConfidence.diff(20).round(2)
    table_data['SignalConfidence'] = table_data.SignalConfidence.round(2)

    table_data = table_data[table_data.data_date == table_data.data_date.max()]
    table_data.sort_values('market_cap',ascending=False,inplace=True)

    table_data = table_data[['ticker','zacks_x_sector_desc','zacks_m_ind_desc','SignalConfidence','delta_1wk','delta_2wk','delta_4wk']]
    table_data = table_data.to_dict(orient='records')

    context = {'chart_data':chart_data,
               'table_data':table_data,
               'current_sector':current_sector_name,
               'sector_selector':sector_form}
    sql.close_connection()
    sql_source.close_connection()

    return render(request, 'site_app/equities_sector_industry_signals.html', context)

@login_required
def equities_latest_signals(request):
    sql = Access_SQL_DB(MySQL_Server,db='equity_models')

    signals = Table('signals_daily_2017_07_01', sql.META, autoload=True)

    today = datetime.datetime.now() 
    signal_data_columns = ['data_date','ticker','close','market_cap','zacks_x_sector_desc','zacks_m_ind_desc','SignalConfidence']

    query = select([signals.c[x] for x in signal_data_columns]).where(((signals.c.data_date >= today-datetime.timedelta(days=7)) & 
                                                                       (signals.c.data_date <= today))) 


    signal_data = pd.read_sql_query(query, sql.ENGINE, index_col=None, parse_dates=['data_date']).sort_index()

    signal_data['SignalDirection'] = signal_data.SignalConfidence.apply(lambda x: 'Long' if x >= EnterLong else 'Short' if x <= EnterShort else 'Neutral')

    signal_data = signal_data[signal_data.SignalDirection.isin(['Long','Short'])]

    signal_data.sort_values('data_date', ascending=False, inplace=True)

    signal_data = signal_data.to_dict(orient='records')

    context = {'signal_data':signal_data}
    sql.close_connection()

    return render(request, 'site_app/equities_latest_signals.html', context)

@login_required
def equities_ticker(request,ticker):
    ticker = ticker.upper()
    signal_data_columns = ['data_date','market_cap','ticker','volume','zacks_x_sector_desc','zacks_m_ind_desc','close','adj_close','SignalConfidence']

    sql = Access_SQL_DB(MySQL_Server,db='equity_models')
    signals = Table('signals_daily_2017_07_01', sql.META, autoload=True)
    query = select([signals.c[x] for x in signal_data_columns]).where(signals.c.ticker ==ticker) 

    st_df = pd.read_sql_query(query, sql.ENGINE, index_col=None, parse_dates=['data_date']).sort_index()

    ## Check if stacked signal data exists
    if (not(len(st_df))):
        template = loader.get_template('site_app/ticker_not_found.html')
        #context = RequestContext(request,{'ticker':ticker})
        context = {'ticker':ticker}
        return HttpResponse(template.render(context))

    st_df['SignalDirection'] = st_df.SignalConfidence.apply(lambda x: None if pd.isnull(x) else 'Long' if x >= EnterLong else 'Short' if x <= EnterShort else 'Neutral')
    st_df.zacks_m_ind_desc = st_df.zacks_m_ind_desc.astype(str).map(lambda x: x.title())

    ## add some info to st_df
    st_df['volume_sma30'] = pd.rolling_mean(st_df.volume,30)
    st_df['daily_average_trading_value'] = st_df['volume_sma30'] * st_df.close

    ## sort and reset index 
    st_df.sort_values('data_date', ascending=True, inplace=True)
    st_df.set_index('data_date',inplace = True) 

    ## latest signal 
    st_df_f = st_df[st_df.SignalDirection.notnull()]
    latest_signal = st_df_f.SignalDirection.iloc[-1]
    latest_signal_date = st_df_f.index[-1].strftime('%m/%d/%Y')

    st_df['data_date'] = st_df.index
    st_df.reset_index(inplace = True,drop=True)

    #convert to JSON for exchange with JS
    chart_data = st_df.to_json(orient='records', date_format='iso') 

    
    context = {'ticker':ticker,
               'latest_bar':st_df.iloc[-1].to_dict(),
               'chart_data':chart_data,
               'latest_signal':latest_signal,
               'latest_signal_date':latest_signal_date}

    sql.close_connection()
    return render(request, 'site_app/equities_ticker.html', context)


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

    signal_data = signal_data[['price_date','sp_close','long_confidence','long_threshold','short_threshold']]
    signal_data.columns = ['Date','sp_close','long_confidence','long_threshold','short_threshold']

    latest_signal = 'Long' if signal_data.long_confidence.iloc[-1] >= signal_data.long_threshold.iloc[-1]/100 else 'Short' if (1-signal_data.long_confidence.iloc[-1]) >= signal_data.short_threshold.iloc[-1]/100 else 'Neutral'
    latest_signal_date = signal_data.Date.iloc[-1].strftime('%m/%d/%Y')

    signal_data = signal_data.to_json(orient='records',date_format='iso')

    context = {'chart_data':signal_data,
               'latest_signal':latest_signal,
               'latest_signal_date':latest_signal_date}

    SQL_CONN.close()
    SQL_ENGINE.dispose()

    return render(request, 'site_app/macro_signals.html', context)


