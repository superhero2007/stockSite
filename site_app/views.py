from django import forms
from django.contrib.auth.decorators import login_required

from django.urls import reverse
from django.shortcuts import render,redirect
from django.conf import settings

from sqlalchemy import create_engine,select,Table, Column, MetaData,sql

import sys
import pandas as pd
import imp
import os
import datetime

from semutils.db_access import Access_SQL_DB, Access_SQL_Source
#mongo = imp.load_source('*', os.path.join(settings.STATIC_ROOT,'AccessMongo.py'))
#sql = imp.load_source('*', os.path.join(settings.STATIC_ROOT,'Access_SQL_Database.py'))


# Create your views here.
from django.http import HttpResponse
from django.template import RequestContext, loader

EnterLong = 0.6
EnterShort = 0.4

@login_required
def search_redirect(request):
    if request.method == 'GET':
        ticker = request.GET.get('ticker','')        
        return redirect(reverse('ticker',args={ticker}))

@login_required
def under_development(request):
    if request.method == 'GET':
        return render(request, 'site_app/under_development.html')

@login_required
def equities_sector_industry_signals(request):
    sql_source = Access_SQL_Source('104.197.188.90')
    sql = Access_SQL_DB('104.197.188.90',db='equity_models')

    sec_master = sql_source.get_sec_master()
    
    sectors = sec_master.zacks_x_sector_desc.unique()

    signals = Table('signals_daily_2017_07_01', sql.META, autoload=True)

    today = datetime.datetime.now() 
    signal_data_columns = ['data_date','ticker','close','market_cap','zacks_x_sector_desc','zacks_m_ind_desc','SignalConfidence']

    query = select([signals.c[x] for x in signal_data_columns]).where(((signals.c.data_date >= today-datetime.timedelta(days=7)) & 
                                                                       (signals.c.data_date <= today)))

    signal_data = pd.read_sql_query(query, sql.ENGINE, index_col=None, parse_dates=['data_date']).sort_index()

    signal_data = signal_data[signal_data.zacks_x_sector_desc==sectors[0]]

    signal_data.sort_values('data_date', ascending=False, inplace=True)

    signal_data = signal_data.to_dict(orient='records')

    class sector_form(forms.Form):
        sectors = forms.ChoiceField(choices=[])
        def __init__(self, sectors):
            super().__init__(sectors)
            self.fields['sectors'].choices = sectors

    all_sectors = sector_form([(0,0),(1,1)])

    context = {'signal_data':signal_data,
               'sector':sectors[0],
               'all_sectors':all_sectors}
    sql.close_connection()

    return render(request, 'site_app/equities_sector_industry_signals.html', context)

@login_required
def equities_latest_signals(request):
    sql = Access_SQL_DB('104.197.188.90',db='equity_models')

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

    sql = Access_SQL_DB('104.197.188.90',db='equity_models')
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


